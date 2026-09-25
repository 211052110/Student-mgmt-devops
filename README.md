# Student Management System — DevOps Pipeline

A minimal Flask + SQLite CRUD app, built to demonstrate a complete DevOps
pipeline for the TAE-II mini project:

```
Developer -> Git Repository -> Jenkins -> Build & Test -> Docker Image -> Deployment -> Monitoring
```

## 1. Project structure

```
student-mgmt-devops/
├── app/                  # Flask application
│   ├── main.py
│   ├── requirements.txt
│   └── templates/index.html
├── tests/                # pytest unit tests
│   └── test_app.py
├── ansible/              # deployment automation
│   ├── deploy.yml
│   └── inventory.ini
├── monitoring/
│   └── prometheus.yml
├── Dockerfile
├── docker-compose.yml
├── Jenkinsfile
└── README.md
```

## 2. Run locally (sanity check, no Docker needed)

```bash
cd app
pip install -r requirements.txt
python main.py
# open http://localhost:5000
```

Run the tests:

```bash
pip install -r tests/requirements-test.txt
pytest -q
```

## 3. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: Student Management System with DevOps pipeline"
git branch -M main
git remote add origin https://github.com/<your-username>/student-mgmt-devops.git
git push -u origin main
```

## 4. Run with Docker

```bash
docker build -t student-mgmt-app .
docker run -p 5000:5000 student-mgmt-app
```

Or bring up the app + monitoring stack together:

```bash
docker-compose up --build
# app:        http://localhost:5000
# prometheus: http://localhost:9090
# grafana:    http://localhost:3000  (login: admin / admin)
```

## 5. Set up Jenkins

Easiest path — run Jenkins itself in Docker (needs Docker socket access so
Jenkins can build images):

```bash
docker run -d --name jenkins \
  -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts
```

1. Open `http://localhost:8080`, unlock with the initial admin password
   (`docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword`).
2. Install suggested plugins, plus the **Docker Pipeline** and **Ansible**
   plugins.
3. Add your Docker Hub credentials under
   *Manage Jenkins → Credentials* with ID `dockerhub-creds`.
4. Create a new **Pipeline** job → point it at your GitHub repo →
   Jenkins will pick up the `Jenkinsfile` automatically.
5. Edit `DOCKERHUB_USER` in the `Jenkinsfile` to your own Docker Hub
   username before your first build.

Each build then: checks out code → installs deps → runs `pytest` →
builds the Docker image → pushes it to Docker Hub → runs the Ansible
playbook to deploy it.

## 6. Deploy to a VM with Ansible (used by the Jenkins "Deploy" stage)

1. Edit `ansible/inventory.ini` with your VM's IP and SSH user.
2. Make sure the Jenkins machine can SSH into the VM (key-based auth).
3. Run manually to test before wiring it into Jenkins:

```bash
ansible-playbook -i ansible/inventory.ini ansible/deploy.yml \
  --extra-vars "image=<your-dockerhub-username>/student-mgmt-app:latest"
```

This installs Docker on the VM if missing, pulls the image, and (re)starts
the container.

## 7. Monitoring

- `/health` — liveness check, used by Docker's `HEALTHCHECK` and can be
  wired into Jenkins/UptimeRobot for external checks.
- `/metrics` — Prometheus-format request counter, scraped by the
  `prometheus` service in `docker-compose.yml`.
- Grafana can be pointed at the Prometheus data source
  (`http://prometheus:9090`) to build a dashboard on top of it.

## 8. What to write up in the TAE-II submission

- **Tools used:** Git/GitHub, Jenkins, Docker, Docker Hub, Ansible,
  Prometheus, Grafana.
- **Pipeline stages:** Checkout → Install & Test (pytest) → Build image →
  Push to registry → Deploy (Ansible) → Monitor (Prometheus/Grafana).
- **Output:** a running Student Management System reachable on port 5000,
  with health/metrics endpoints and a CRUD UI.
