package main

import (
	"bufio"
	"context"
	"fmt"
	"strconv"
	"strings"

	"google3/base/go/google"
	"google3/base/go/log"
	"google3/base/go/runfiles"
	"google3/file/base/go/file"
)

var (
	borgTemplate = `
job encode_parser {
  name = 'encode_parser_%d_' + real_username()
  runtime = { cell = 'jc' }
  permissions = { user = 'datcom' }
  package_binary = 'bin/parser'
  packages {
    package bin {
      blaze_label =
          '//datacommons/mcf/encode:encode_parser_mpm'
    }
  }
  args = {
    parallel = 1
    experiment_dirs = '%s'
		output_root = '/cns/jv-d/home/datcom/v3_mcf/encode/mcf/'
  }
  requirements = {
    milligcu = 2000
    ram = 4G
    disk = 1G
    autopilot = false
  }
  appclass = { type = 'LATENCY_TOLERANT_PRIMARY' }
  scheduling = { priority = 119 }
}
`
	outputDirPath = "/google/src/cloud/antaresc/encode-scraper/google3/datacommons/mcf/encode"
)

func main() {
	google.Init()
	ctx := context.Background()

	fin, err := file.OpenRead(ctx,
		runfiles.Path("google3/datacommons/mcf/encode/enc_list.txt"))
	if err != nil {
		log.Fatal(err)
	}
	defer fin.IO(ctx).Close()

	var runFile string
	var killFile string
	idx := 0
	cnt := 0
	folderNames := []string{}

	scanner := bufio.NewScanner(fin.IO(ctx))
	for scanner.Scan() {
		folderNames = append(folderNames, scanner.Text())
		cnt++

		if cnt >= 150 {
			idx++
			cnt = 0

			borgFile := fmt.Sprintf(borgTemplate, idx, strings.Join(folderNames, ","))
			outFilePath := fmt.Sprintf("%s/parser_%d.borg", outputDirPath, idx)
			if err := file.WriteFile(ctx, outFilePath,
				[]byte(borgFile)); err != nil {
				log.Exitf("file.WriteFile(%s) = %s", outFilePath, err)
			}

			runFile += "blaze build -c opt :encode_parser_mpm\n"
			runFile += fmt.Sprintf("borgcfg parser_%d.borg reload --skip_confirmation\n",
				idx)

			killFile += fmt.Sprintf(
				"borg --borg=jc --user=datcom canceljob encode_parser_%d_wsws\n", idx)
			killFile += "echo killed " + strconv.Itoa(idx) + "\n"

			folderNames = []string{}
		}
	}
	if err := scanner.Err(); err != nil {
		log.Fatal(err)
	}

	if err := file.WriteFile(ctx, fmt.Sprintf("%s/run.sh", outputDirPath),
		[]byte(runFile)); err != nil {
		log.Exitf("file.WriteFile(runFile) = %s", err)
	}

	if err := file.WriteFile(ctx, fmt.Sprintf("%s/kill.sh", outputDirPath),
		[]byte(killFile)); err != nil {
		log.Exitf("file.WriteFile(killFile) = %s", err)
	}
}
