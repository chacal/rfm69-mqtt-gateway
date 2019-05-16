docker:
	@docker build -t jihartik/rfm69-mqtt-gateway .

docker-push:
	@docker push jihartik/rfm69-mqtt-gateway:latest