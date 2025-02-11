.PHONY: \
	checkAwsCredentials createPythonEnvironment createTerraformBackend installPythonRequirements installTypeScriptRequirements \
	deploy destroy \
	clean cleanPython cleanTerraform cleanTypeScript \
	terraformInit terraformFmtValidate terraformPlan terraformApply terraformDestroy \
	runIngestLocal runApiLocal runUiLocal \
	help

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))


#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Check AWS credentials
checkAwsCredentials:
	@if [ -z "$$AWS_PROFILE" ]; then \
		if aws sts get-caller-identity >/dev/null 2>&1; then \
			export AWS_PROFILE=default; \
			echo "AWS credentials detected, setting AWS_PROFILE=default"; \
		else \
			echo "Error: No AWS credentials available."; \
			echo "Please either:"; \
			echo "  1. Set AWS_PROFILE using 'export AWS_PROFILE=your-profile'"; \
			echo "  2. Ensure you're running on an EC2 instance with an appropriate instance role"; \
			exit 1; \
		fi \
	fi


## Set up Python interpreter environment
createPythonEnvironment:
	python3 -m venv .venv
	@printf "New virtual environment created. To activate run: 'source .venv/bin/activate'\n"


## Create Terraform backend configuration
createTerraformBackend: checkAwsCredentials
	@sh ${PROJECT_DIR}/scripts/create_tf_backend.sh


## Install Python dependencies for development
installPythonRequirements:
	@echo "Installing Python dependencies..."
	@( \
		echo "Step 1: Trying standard pip upgrade..." && \
		pip3 install pip --upgrade && \
		pip3 install -r requirements-dev.txt \
	) || ( \
		echo "Standard installation failed. Attempting pip reinstallation..." && \
		echo "Step 2: Running get_pip.py..." && \
		python3 "${PROJECT_DIR}/scripts/get_pip.py" --force-reinstall || true && \
		echo "Step 3: Trying pip upgrade again..." && \
		python3 -m pip install --upgrade pip && \
		echo "Step 4: Installing requirements..." && \
		python3 -m pip install -r requirements-dev.txt \
	) || ( \
		echo "All attempts failed. Trying alternative approach..." && \
		curl https://bootstrap.pypa.io/get-pip.py -o get_pip.py && \
		python3 get_pip.py && \
		python3 -m pip install -r requirements-dev.txt && \
		rm get_pip.py \
	)


## Install TypeScript dependencies for development
installTypeScriptRequirements:
	npm install --prefix $(PROJECT_DIR)/projects/frontend


## Install Python and TypeScript dependencies for development
install: installPythonRequirements installTypeScriptRequirements


## Delete all local compiled Python files and related artifacts
cleanPython:
	@find . -type f -name "*.py[co]" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type d -name "dist" -exec rm -rf {} +
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@find . -type d -name ".tox" -exec rm -rf {} +


## Delete all local Terraform files and related artifacts
cleanTerraform:
	@find . -type f -name ".terraform.lock.hcl" -delete
	@find . -type f -name "terraform.tfstate" -delete
	@find . -type f -name "terraform.tfstate.backup" -delete
	@find . -type f -name "crash.log" -delete
	@find . -type f -name "*.tfplan" -delete
	@find . -type d -name ".terraform" -exec rm -rf {} +


## Delete local TypeScript artifacts and related folders
cleanTypeScript:
	@find . -type d -name "node_modules" -exec rm -rf {} +
	@find . -type f -name "*.js.map" -delete
	@find . -type d -name "dist" -exec rm -rf {} +
	@find . -type d -name "build" -exec rm -rf {} +
	@find . -type d -name ".tscache" -exec rm -rf {} +
	@find . -type d -name ".jest_cache" -exec rm -rf {} +


## Delete all relevant files
clean: cleanPython cleanTerraform cleanTypeScript


## Initialize Terraform configuration
terraformInit: createTerraformBackend
	@echo "Initializing Terraform..."
	@terraform -chdir=$(PROJECT_DIR)/projects/infra init -backend-config="backend.tfvars"


## Format and validate Terraform code
terraformFmtValidate:
	@echo "Formatting Terraform code..."
	@terraform -chdir=$(PROJECT_DIR)/projects/infra fmt -recursive
	@echo "Validating Terraform code..."
	@terraform -chdir=$(PROJECT_DIR)/projects/infra validate


## Plan Terraform configuration
terraformPlan: terraformFmtValidate checkAwsCredentials
	@echo "Planning Terraform changes..."
	@terraform -chdir=$(PROJECT_DIR)/projects/infra plan -var-file="$(PROJECT_DIR)/dev.tfvars" -out="dev.tfplan"


## Apply Terraform configuration
terraformApply: terraformFmtValidate checkAwsCredentials
	@echo "Applying Terraform changes..."
	@terraform -chdir=$(PROJECT_DIR)/projects/infra apply "dev.tfplan"


## Destroy Terraform infrastructure
terraformDestroy: terraformFmtValidate checkAwsCredentials
	@echo "Destroying Terraform infrastructure..."
	@terraform -chdir=$(PROJECT_DIR)/projects/infra destroy -auto-approve -var-file="$(PROJECT_DIR)/dev.tfvars"


## Run data ingest locally - TODO: ADD THESE
# runIngestLocal: checkAwsCredentials
# 	@if [ -z "$(JOB_ID)" ]; then \
# 		echo "Error: JOB_ID is required. Usage: make runIngestLocal JOB_ID=your-job-id"; \
# 		exit 1; \
# 	fi
# 	@if [ -z "$(AWS_REGION)" ]; then \
# 		echo "Error: AWS_REGION is required. Usage: make runIngestLocal AWS_REGION=your-aws-region"; \
# 		exit 1; \
# 	fi
# 	@if [ -z "$(DATA_DIR)" ]; then \
# 		echo "Error: DATA_DIR is required. Usage: make runIngestLocal DATA_DIR=your-local-results-directory"; \
# 		exit 1; \
# 	fi
# 	$(eval TF_OUTPUTS := $(shell cd terraform && terraform output -json))
# 	@UPLOADS_BUCKET_NAME=$(shell echo '$(TF_OUTPUTS)' | jq -r '.uploads_bucket_name.value') \
# 	RESULTS_BUCKET_NAME=$(shell echo '$(TF_OUTPUTS)' | jq -r '.results_bucket_name.value') \
# 	WORKS_TABLE_NAME=$(shell echo '$(TF_OUTPUTS)' | jq -r '.works_table_name.value') \
# 	JOB_ID=$(JOB_ID) \
# 	python3 $(PROJECT_DIR)/projects/infra/modules/ecs/src/main.py


# ## Run dev proxy API locally - TODO: ADD THESE
# runApiLocal: checkAwsCredentials
# 	@python3 $(PROJECT_DIR)/scripts/local_proxy_api_server.py


# ## Run dev UI locally - TODO: ADD THESE
# runUiLocal:
# 	@npm run dev --prefix $(PROJECT_DIR)/projects/frontend


#################################################################################
# SELF DOCUMENTING COMMANDS                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>

help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=35 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
