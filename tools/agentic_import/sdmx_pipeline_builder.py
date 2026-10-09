# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Builder for the SDMX agentic import pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Sequence

from absl import logging

from tools.agentic_import.pipeline import Pipeline, Step
from tools.agentic_import.sdmx_pipeline_config import PipelineConfig
from tools.agentic_import.sdmx_pipeline_steps import (
    CreateDcConfigStep, CreateSampleStep, CreateSchemaMapStep, DownloadDataStep,
    DownloadMetadataStep, ExtractMetadataStep, ProcessFullDataStep)
from tools.agentic_import.state_handler import PipelineState


@dataclass(frozen=True)
class StepDecision:
    """Represents whether a step will run and why."""

    RUN: ClassVar[str] = "RUN"
    SKIP: ClassVar[str] = "SKIP"

    step_name: str
    decision: str
    reason: str


@dataclass(frozen=True)
class BuildResult:
    """Output of planning that includes the pipeline and per-step decisions."""

    pipeline: Pipeline
    decisions: list[StepDecision]


class PipelineBuilder:

    def __init__(self,
                 *,
                 config: PipelineConfig,
                 state: PipelineState,
                 steps: Sequence[Step],
                 critical_input_hash: str | None = None) -> None:
        self._config = config
        self._state = state
        self._steps = steps
        self._critical_input_hash = critical_input_hash

    def build(self) -> BuildResult:
        if self._config.run.run_only:
            if self._config.run.run_from or self._config.run.run_until:
                raise ValueError(
                    "run_only cannot be combined with run_from/run_until")
            planned, decisions = self._plan_run_only(self._config.run.run_only)
            logging.info("Built SDMX pipeline with %d steps", len(planned))
            return BuildResult(pipeline=Pipeline(steps=planned),
                               decisions=decisions)
        if self._config.run.force:
            logging.info("Force flag set; scheduling all SDMX steps")
            planned, decisions = self._plan_all_steps(
                "Force flag set; scheduling this step")
        elif self._hash_changed():
            logging.info("Critical inputs changed; scheduling all SDMX steps")
            planned, decisions = self._plan_all_steps(
                "Critical inputs changed; scheduling this step")
        else:
            planned, decisions = self._plan_incremental()
        planned, decisions = self._apply_range_filter(planned, decisions)
        logging.info("Built SDMX pipeline with %d steps", len(planned))
        return BuildResult(pipeline=Pipeline(steps=planned),
                           decisions=decisions)

    def _plan_run_only(self,
                       run_only: str) -> tuple[list[Step], list[StepDecision]]:
        planned: list[Step] = []
        decisions: list[StepDecision] = []
        for step in self._steps:
            if step.name == run_only:
                planned.append(step)
                decisions.append(
                    StepDecision(
                        step_name=step.name,
                        decision=StepDecision.RUN,
                        reason=(f"run_only={run_only} requested; running only "
                                "this step"),
                    ))
            else:
                decisions.append(
                    StepDecision(
                        step_name=step.name,
                        decision=StepDecision.SKIP,
                        reason=(f"run_only={run_only} requested; skipping "
                                "this step"),
                    ))
        if not planned:
            raise ValueError(f"run_only step not found: {run_only}")
        return planned, decisions

    def _plan_all_steps(self,
                        reason: str) -> tuple[list[Step], list[StepDecision]]:
        planned: list[Step] = []
        decisions: list[StepDecision] = []
        for step in self._steps:
            planned.append(step)
            decisions.append(
                StepDecision(step_name=step.name,
                             decision=StepDecision.RUN,
                             reason=reason))
        return planned, decisions

    def _plan_incremental(self) -> tuple[list[Step], list[StepDecision]]:
        return self._plan_incremental_steps(self._steps)

    def _plan_incremental_steps(
            self,
            steps: Sequence[Step]) -> tuple[list[Step], list[StepDecision]]:
        planned: list[Step] = []
        decisions: list[StepDecision] = []
        schedule_all_remaining = False
        previous: Step | None = None
        for step in steps:
            if schedule_all_remaining:
                planned.append(step)
                decisions.append(
                    StepDecision(
                        step_name=step.name,
                        decision=StepDecision.RUN,
                        reason=("Upstream step triggered rerun for remaining "
                                "steps"),
                    ))
                previous = step
                continue

            prev_state = self._state.steps.get(step.name)
            if prev_state is None:
                needs_run = True
                reason = "No previous state recorded; scheduling step"
            elif prev_state.status != "succeeded":
                needs_run = True
                reason = (f"Previous run status was {prev_state.status}; "
                          "rerunning step")
            elif prev_state.version != step.version:
                needs_run = True
                reason = (f"Step version changed from {prev_state.version} to "
                          f"{step.version}; rerunning step")
            else:
                needs_run = False
                reason = ("Previous run succeeded with same version; step is "
                          "up-to-date")

            if not needs_run and previous is not None:
                if self._predecessor_newer(previous, step):
                    needs_run = True
                    reason = (f"Previous step {previous.name} finished more "
                              "recently; rerunning downstream steps")

            if needs_run:
                planned.append(step)
                decisions.append(
                    StepDecision(step_name=step.name,
                                 decision=StepDecision.RUN,
                                 reason=reason))
                schedule_all_remaining = True
            else:
                decisions.append(
                    StepDecision(step_name=step.name,
                                 decision=StepDecision.SKIP,
                                 reason=reason))
            previous = step

        if not planned:
            logging.info("No steps scheduled.")
        return planned, decisions

    def _resolve_step_index(self, name: str, flag_name: str) -> int:
        for index, step in enumerate(self._steps):
            if step.name == name:
                return index
        raise ValueError(f"{flag_name} step not found: {name}")

    def _range_skip_reason(self) -> str:
        parts = []
        if self._config.run.run_from:
            parts.append(f"run_from={self._config.run.run_from}")
        if self._config.run.run_until:
            parts.append(f"run_until={self._config.run.run_until}")
        suffix = " ".join(parts) if parts else "range"
        return f"Outside requested range ({suffix})"

    def _select_range(self) -> tuple[int, int, bool]:
        run_from = self._config.run.run_from
        run_until = self._config.run.run_until
        if not run_from and not run_until:
            return 0, len(self._steps) - 1, False
        start = 0
        end = len(self._steps) - 1
        if run_from:
            start = self._resolve_step_index(run_from, "run_from")
        if run_until:
            end = self._resolve_step_index(run_until, "run_until")
        if start > end:
            raise ValueError(
                f"run_from={run_from} must not come after run_until={run_until}"
            )
        return start, end, True

    def _apply_range_filter(
        self,
        planned: list[Step],
        decisions: list[StepDecision],
    ) -> tuple[list[Step], list[StepDecision]]:
        start, end, has_range = self._select_range()
        if not has_range:
            return planned, decisions
        decisions_by_name = {
            decision.step_name: decision for decision in decisions
        }
        in_range = {step.name for step in self._steps[start:end + 1]}
        filtered_planned = [step for step in planned if step.name in in_range]
        filtered_decisions: list[StepDecision] = []
        outside_reason = self._range_skip_reason()
        for index, step in enumerate(self._steps):
            if start <= index <= end:
                filtered_decisions.append(decisions_by_name[step.name])
            else:
                decision = decisions_by_name[step.name]
                filtered_decisions.append(
                    StepDecision(step_name=step.name,
                                 decision=StepDecision.SKIP,
                                 reason=self._format_outside_range_reason(
                                     outside_reason, decision)))
        return filtered_planned, filtered_decisions

    def _format_outside_range_reason(self, outside_reason: str,
                                     decision: StepDecision) -> str:
        return (f"{outside_reason}; original decision={decision.decision}; "
                f"original reason={decision.reason}")

    def _hash_changed(self) -> bool:
        if not self._critical_input_hash:
            return False
        previous = self._state.critical_input_hash
        if not previous:
            return True
        return previous != self._critical_input_hash

    def _predecessor_newer(self, prev_step: Step, step: Step) -> bool:
        prev_state = self._state.steps.get(prev_step.name)
        curr_state = self._state.steps.get(step.name)
        if prev_state is None or prev_state.ended_at_ts is None:
            return False
        if curr_state is None:
            return True
        if curr_state.status != "succeeded":
            return True
        if curr_state.ended_at_ts is None:
            return True
        return prev_state.ended_at_ts > curr_state.ended_at_ts


def build_steps(config: PipelineConfig) -> list[Step]:
    """Constructs the hard-coded list of canonical steps."""
    return [
        DownloadDataStep(name="download-data", config=config),
        DownloadMetadataStep(name="download-metadata", config=config),
        ExtractMetadataStep(name="extract-metadata", config=config),
        CreateSampleStep(name="create-sample", config=config),
        CreateSchemaMapStep(name="create-schema-mapping", config=config),
        ProcessFullDataStep(name="process-full-data", config=config),
        CreateDcConfigStep(name="create-dc-config", config=config),
    ]


def _log_step_decisions(decisions: Sequence[StepDecision]) -> None:
    for decision in decisions:
        logging.info("step=%s decision=%s reason=%s", decision.step_name,
                     decision.decision, decision.reason)


def build_sdmx_pipeline(*,
                        config: PipelineConfig,
                        state: PipelineState,
                        steps: Sequence[Step] | None = None,
                        critical_input_hash: str | None = None) -> Pipeline:
    builder_steps = steps if steps is not None else build_steps(config)
    builder = PipelineBuilder(config=config,
                              state=state,
                              steps=builder_steps,
                              critical_input_hash=critical_input_hash)
    result = builder.build()
    _log_step_decisions(result.decisions)
    return result.pipeline
