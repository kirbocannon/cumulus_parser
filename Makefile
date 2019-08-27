DOCKER_IMG_NAME = cumulus_parser
DOCKER_TAG = 0.1

CONTAINER_NAME = cumulus_parser

.PHONY: build
build:
	docker build -t $(DOCKER_IMG):$(DOCKER_TAG) .

.PHONY: start
start:
	docker start $(CONTAINER_NAME)

.PHONY: run
run:
	docker run -itd \
	--name $(CONTAINER_NAME) \
	$(DOCKER_IMG_NAME):$(DOCKER_TAG) 

.PHONY: rm
rm:
	docker rm -f $(CONTAINER_NAME)
