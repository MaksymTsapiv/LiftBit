# LiftBit

## Prerequisites
- Docker
- Docker Compose

## Usage

### Starting the containers
To (re)build images and start the containers, run the following in the project root directory:
```bash
$ PORT=3000 docker compose up --build -d
```
The endpoint will be available at port 3000 on any interface (e.g. http://localhost:3000).

### Stopping the containers
To stop the containers, run the following in the project root directory:
```bash
$ docker compose down
```

