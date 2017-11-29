node('docker'){
    stage "Container Prep"
        def mycontainer = docker.image('elastest/ci-docker-compose-py-siblings:latest')
        mycontainer.pull() // make sure we have the latest available from Docker Hub

        mycontainer.inside("-u jenkins -v /var/run/docker.sock:/var/run/docker.sock:rw") {

            git 'https://github.com/elastest/elastest-service-manager'

            stage "Setup test environment"
                sh 'rm -rf /home/ubuntu/workspace/elastest-service-manager/esm/.tox'

                try {
                   sh "docker rm -f mongo"
                } catch(e) {
                   echo "Error: $e"
                }

                sh "docker run --name mongo -d --rm mongo"
                sh "docker inspect mongo"
                sh "docker network list"
                sh "docker network connect elastest_elastest mongo"
                mongoIP = sh (
                    script: 'docker inspect --format=\\"{{.NetworkSettings.Networks.elastest_elastest.Gateway}}\\" mongo',
                    returnStdout: true
                ).trim()
                echo "Mongo container IP=${mongoIP}"

                mongoIP = sh (
                    script: 'docker inspect --format \\"{{ .NetworkSettings.IPAddress }}\\" mongo',
                    returnStdout: true
                ).trim()
                echo "Mongo container IP=${mongoIP}"

            stage "Unit tests"
                echo ("Starting unit tests...")

                // sh "docker inspect ${c.id}"
                // sh "docker logs ${c.id}"
                // sh 'tox'
                // step([$class: 'JUnitResultArchiver', testResults: '**/nosetests.xml'])

            stage "Build image - Package"
                echo ("building...")
                // def myimage = docker.build("elastest/esm:latest")

            stage "Publish"
                echo ("Publishing as all tests succeeded...")
                // withCredentials([[$class: 'UsernamePasswordMultiBinding', credentialsId: 'elastestci-dockerhub',
                // usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {
                //     sh 'docker login -u "$USERNAME" -p "$PASSWORD"'
                //     myimage.push()
                // }
        }
}
