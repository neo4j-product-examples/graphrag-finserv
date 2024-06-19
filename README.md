# GraphRAG Finserv Example
GraphRAG Examples for Financial Services

### __:warning: This Repo is Work in Progress :warning:__


## App Deployment

These directions are written for GCP but should be repeatable with minor changes on other cloud providers. 

### 1 Create Instance
* Create a Google Cloud instance.
* Then create firewall rules to allow traffic on ports 8080 and 8501
* Next resize the disk with the below command (often defaults or for 10GB disk which will cause problems).
`gcloud compute disks resize <boot disk name> --size 100`
Then restart the instance for the boot disk change to take effect

### 2 Setup & Config
Easiest with root access for demo purposes, so first:

    sudo su

Then you'll need to install git and clone this repo:

    apt install -y git
    mkdir -p /app
    cd /app
    git clone https://github.com/neo4j-product-examples/graphrag-finserv.git
    cd graphrag-finserv

Let's install python & pip:

    apt install -y python
    apt install -y pip

Now, install docker [per these directions](https://docs.docker.com/engine/install/debian/#install-using-the-repository)

Then install docker-compose
    
    apt install docker-compose

Now update the configs in a `.env` file

    #Neo4j
    NEO4J_URI=neo4j+s://<xxxxxxxx>.databases.neo4j.io
    NEO4J_USERNAME=neo4j
    #NEO4J_DATABASE=neo4j
    NEO4J_PASSWORD=<password>
    
    #OpenAI
    OPENAI_API_KEY=<sk-...>


### 3 Run
build and run the container with below command (the first time can take a while to build)

    docker-compose up

Optionally, you can run in a detached state to ensure the app continues even if you disconnect from the vm instance:

    docker-compose up -d

To stop the app run

    docker-compose down

