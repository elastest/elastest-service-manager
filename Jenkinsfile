node('docker'){
    stage "Container Prep"
        
        echo("the node is up")
        def mycontainer = docker.image('elastest/ci-docker-compose-py-siblings:latest')
        mycontainer.pull() // make sure we have the latest available from Docker Hub
        
        mycontainer.inside("-u jenkins -v /var/run/docker.sock:/var/run/docker.sock:rw") {

            sh 'rm -rf /home/ubuntu/workspace/elastest-service-manager/esm/.tox'

            git 'https://github.com/elastest/elastest-service-manager'

            stage "Setup test environment"
                echo 'nop'
                // echo 'creating default elastest network'
                // sh 'docker network create elastest'
                // echo 'creating local mongodb instance'
                // sh 'docker run -d -p 27017:27017 -v /tmp/mongodata:/data/db mongo'

            stage "Unit tests"
                echo ("Starting unit tests...")
                sh 'tox'
                step([$class: 'JUnitResultArchiver', testResults: '**/nosetests.xml'])

            stage "Build image - Package"
                // maybe use packer.io to build both container and VM images?
                echo ("building...")
                def myimage = docker.build("elastest/esm:latest")

            stage "Execute docker compose"
                echo ("nop")
                // sh 'docker-compose -f docker-compose-no-mon.yml up -d --build'
                // get the ESM IP address
                // poll for ESM availability, curl
                // execute a set of tests against the ESM endpoint

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
