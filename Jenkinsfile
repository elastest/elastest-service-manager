node('docker'){
    stage "Container Prep"
        
        echo("the node is up")
        echo("Building docker-compose-py-siblings locally")
        git 'https://github.com/elastest/ci-images'
        sh "ls"
        def mycontainer = docker.build('elastest/ci-docker-compose-py-siblings:latest -f ci-images/ci-docker-compose-py-siblings/Dockerfile')
        // mycontainer.pull() // make sure we have the latest available from Docker Hub
        
        mycontainer.inside("-u jenkins -v /var/run/docker.sock:/var/run/docker.sock:rw") {
            git 'https://github.com/elastest/elastest-service-manager'

            stage "Setup test environment"
                sh 'rm -rf /home/ubuntu/workspace/elastest-service-manager/esm/.tox'

            stage "Unit tests"
                echo ("Starting unit tests...")
                sh 'tox'
                step([$class: 'JUnitResultArchiver', testResults: '**/nosetests.xml'])

            stage "Build image - Package"
                // maybe use packer.io to build both container and VM images?
                echo ("building...")
                def myimage = docker.build("elastest/esm:0.5.0-beta")

            // stage "Execute docker compose"
                // echo ("nop")

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
