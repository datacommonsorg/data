# Data Commons Schema MCF Files

This directory contains the MCF nodes for all defined schemas in Data Commons.
These files are kept in-sync with the Google repository via Copybara. Changes
inside Google are immediately copied here. Approved GitHub pull requests are
sent to the Google respository, where it is tested; if approved, the PR will
merge into both the Google and GitHub repository.

## Overview

- [schema.mcf](schema.mcf) contains MCF representation of Schema.org schemas.
- [dcschema.mcf](dcschema.mcf) contains general Data Commons classes and
properties.
- [dcschema_enum_classes.mcf](dcschema_enum_classes.mcf) contains Data Commons enum classes.
- [dcschema_enum_instances.mcf](dcschema_enum_instances.mcf) contains Data Commons enum instances.
- [enum_specializations.mcf](enum_specializations.mcf) contains all enum `specializationOf` relationships.
  Please handle this file with care.
- All other MCF files are source or domain specific.
