node('docker'){
    stage "Container Prep"
        def mycontainer = docker.image('elastest/ci-docker-compose-py-siblings:latest')
        mycontainer.pull() // make sure we have the latest available from Docker Hub

        mycontainer.inside("-u jenkins -v /var/run/docker.sock:/var/run/docker.sock:rw") {

            git 'https://github.com/elastest/elastest-service-manager'

            stage "Setup test environment"
                sh 'rm -rf /home/ubuntu/workspace/elastest-service-manager/esm/.tox'

            stage "Unit tests"
                echo ("Starting unit tests...")
                sh 'tox'
                step([$class: 'JUnitResultArchiver', testResults: '**/nosetests.xml'])

            stage "Build image - Package"
                echo ("building...")
                def myimage = docker.build("elastest/esm:0.5.0-beta")

            stage "Publish"
                echo ("Publishing as all tests succeeded...")
                withCredentials([[$class: 'UsernamePasswordMultiBinding', credentialsId: 'elastestci-dockerhub',
                usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {
                    sh 'docker login -u "$USERNAME" -p "$PASSWORD"'
                    myimage.push()
                }
        }
}
