
#################################
# Docker targets
#################################
# .PHONY: clean-image
# clean-image: version-check
#  @echo "+ $@"
#  @docker rmi ${HUB_NAMESPACE}/${IMAGE_NAME}:latest  || true
#  @docker rmi ${HUB_NAMESPACE}/${IMAGE_NAME}:${VERSION}  || true

# .PHONY: image
# image: version-check
#  @echo "+ $@"
#  @docker build -t ${HUB_NAMESPACE}/${IMAGE_NAME}:${VERSION} -f ./${DOCKERFILE} .
#  @docker tag ${HUB_NAMESPACE}/${IMAGE_NAME}:${VERSION} ${HUB_NAMESPACE}/${IMAGE_NAME}:latest
#  @echo 'Done.'
#  @docker images --format '{{.Repository}}:{{.Tag}}\t\t Built: {{.CreatedSince}}\t\tSize: {{.Size}}' | \
#        grep ${IMAGE_NAME}:${VERSION}

.PHONY: images
images:
	docker build -t "chainsail-celery-worker:latest" -f ./docker/celery/Dockerfile .
	docker build -t "chainsail-scheduler:latest" -f ./docker/scheduler/Dockerfile .
	docker build -t "chainsail-nginx:latest" -f ./docker/nginx/Dockerfile .
	docker build -t "chainsail-client:latest" -f app/client/Dockerfile app/client
	docker build -t chainsail-user-code:latest -f docker/user-code/Dockerfile .
	docker build -t httpstan-server:latest -f docker/httpstan-server/Dockerfile .
	docker build -t chainsail-mpi-node-k8s:latest -f docker/node/Dockerfile .