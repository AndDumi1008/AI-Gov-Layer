# AI Governance Layer PoC — convenience targets. Run from the repository root.
COMPOSE = docker compose -f stack/docker-compose.yml
PROFILES ?= --profile mock

.PHONY: help bootstrap up down logs ps test policy-test gateway-test demo sandbox-image clean

help:
	@grep -E '^[a-z-]+:' Makefile | cut -d: -f1 | tr '\n' ' '; echo

bootstrap:          ## first run: .env, DNS zone, build and start (mock model)
	./stack/bootstrap.sh $(PROFILES)

up:                 ## start the stack
	$(COMPOSE) $(PROFILES) up -d --build

down:
	$(COMPOSE) $(PROFILES) down

clean:              ## stop and delete volumes (audit store included — demo only)
	$(COMPOSE) --profile mock --profile model --profile edge down -v

logs:
	$(COMPOSE) logs -f --tail=100 gateway opa egress-proxy

ps:
	$(COMPOSE) ps

policy-test:        ## opa unit tests
	docker run --rm -v "$(PWD)/stack/policy:/policy:ro" openpolicyagent/opa:1.4.2-static test /policy -v

gateway-test:       ## gateway unit tests (DLP, hash chain)
	$(COMPOSE) build gateway && $(COMPOSE) run --rm --no-deps --entrypoint pytest gateway -q tests

test: policy-test gateway-test

sandbox-image:
	docker build -t agl-sandbox:latest stack/sandbox

demo:               ## run scenarios S1–S26 (Tier 1 subset) and write evidence/
	./demo/run-scenarios.sh

# SERVER (Windows + WSL2 + NVIDIA): GPU model tier and edge services
up-server:
	$(COMPOSE) -f stack/docker-compose.gpu.yml --profile model --profile edge up -d --build
	docker exec agl-ollama-1 ollama pull $$(grep -E '^AGL_LOCAL_MODEL=' stack/.env | cut -d= -f2)

# Demo against SERVER from the Mac (see demo/DEMO.md)
demo-server:        ## run the suite against SERVER and build the evidence report
	./demo/run-server.sh
demo-server-reset:  ## logged control-plane reset on SERVER, then the suite and report
	./demo/run-server.sh --reset
demo-report:        ## rebuild the HTML report for the latest evidence folder
	python3 demo/report.py "$$(ls -d evidence/run-* | tail -1)" > "$$(ls -d evidence/run-* | tail -1)/report.html" && echo "$$(ls -d evidence/run-* | tail -1)/report.html"
demo-worm:          ## show the WORM audit store live on SERVER (mc): retention, versions, refused delete
	DOCKER_CONTEXT=server ./demo/show-worm.sh
