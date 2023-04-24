
#################################
# Docker targets
#################################
.PHONY: images
images:
	@echo "Building docker images..."
	docker build -t "${IMAGE_PREFIX}chainsail-celery-worker:latest" -f ./docker/celery/Dockerfile .
	docker build -t "${IMAGE_PREFIX}chainsail-scheduler:latest" -f ./docker/scheduler/Dockerfile .
	docker build -t "${IMAGE_PREFIX}chainsail-nginx:latest" -f ./docker/nginx/Dockerfile .
	docker build -t "${IMAGE_PREFIX}chainsail-user-code:latest" -f docker/user-code/Dockerfile .
	docker build -t "${IMAGE_PREFIX}chainsail-httpstan-server:latest" -f docker/httpstan-server/Dockerfile .
	docker build -t "${IMAGE_PREFIX}chainsail-mpi-node-k8s:latest" -f docker/node/Dockerfile .
	docker build -t "${IMAGE_PREFIX}chainsail-mcmc-stats-server:latest" -f docker/mcmc-stats-server/Dockerfile .
	@echo "Done."

.PHONY: push-images
push-images: images
	@echo "Pushing docker images..."
	docker push "${IMAGE_PREFIX}chainsail-celery-worker:latest"
	docker push "${IMAGE_PREFIX}chainsail-scheduler:latest"
	docker push "${IMAGE_PREFIX}chainsail-nginx:latest"
	docker push "${IMAGE_PREFIX}chainsail-user-code:latest"
	docker push "${IMAGE_PREFIX}chainsail-httpstan-server:latest"
	docker push "${IMAGE_PREFIX}chainsail-mpi-node-k8s:latest"
	docker push "${IMAGE_PREFIX}chainsail-mcmc-stats-server:latest"
	@echo "Done."
