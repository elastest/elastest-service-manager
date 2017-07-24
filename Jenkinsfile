node('docker'){
    stage "Container Prep"
        
        echo("the node is up")
        def mycontainer = docker.image('elastest/docker-compose-py-siblings:latest')
        mycontainer.pull() // make sure we have the latest available from Docker Hub
        
        mycontainer.inside("-u jenkins -v /var/run/docker.sock:/var/run/docker.sock:rw") {

            git 'https://github.com/elastest/elastest-service-manager'
            
            stage "Unit tests"
                // TODO: add DOCKER_TESTS=YES and MONGODB_TESTS=YES env vars - can only be done with mongodb already running
                echo ("Starting unit tests...")
                sh 'docker network create elastest'
                sh 'tox'
                step([$class: 'JUnitResultArchiver', testResults: '**/nosetests.xml'])

            stage "Build image - Package"
                // maybe use packer.io to build both container and VM images?
                echo ("building...")
                def myimage = docker.build("elastest/elastest-service-manager")

            stage "Execute docker compose"
                echo ("nop")
                // sh 'docker-compose -f docker-compose.yml up -d --build'

            stage "Publish"
                echo ("Publishing as all tests succeeded...")
                //this is work around as withDockerRegistry is not working properly
                withCredentials([[$class: 'UsernamePasswordMultiBinding', credentialsId: 'elastestci-dockerhub',
                usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {
                    sh 'docker login -u "$USERNAME" -p "$PASSWORD"'
                    myimage.push()
                }
        }
}