node('docker'){
    stage "Container Prep"
        def mycontainer = docker.image('elastest/ci-docker-compose-py-siblings:latest')
        mycontainer.pull() // make sure we have the latest available from Docker Hub

        mycontainer.inside("-u jenkins -v /var/run/docker.sock:/var/run/docker.sock:rw") {

            git 'https://github.com/elastest/elastest-service-manager'

            stage ("Setup test environment"){
                sh 'rm -rf /home/ubuntu/workspace/elastest-service-manager/esm/.tox'

                try {
                   sh "docker network create elastest_elastest"
                } catch(e) {
                   echo "Error: $e"
                }

                def containerId = sh(
                    script: 'cat /proc/self/cgroup | grep "docker" | sed s/\\\\//\\\\n/g | tail -1',
                    returnStdout: true
                ).trim()
                echo "containerId = ${containerId}"
                sh "docker network list"
                sh "docker network connect elastest_elastest "+ containerId

                try {
                   sh "docker rm -f mongo"
                } catch(e) {
                   echo "Error: $e"
                }

                sh "docker run --name mongo -d --rm mongo:latest"
                sh "docker network connect elastest_elastest mongo"
                mongoIP = sh (
                    script: 'docker inspect --format=\\"{{.NetworkSettings.Networks.elastest_elastest.IPAddress}}\\" mongo',
                    returnStdout: true
                ).trim()
                mongoIP = mongoIP.substring(1, mongoIP.length()-1)
                echo "Mongo container IP=${mongoIP}"

                try {
                   sh "docker rm -f mysql"
                } catch(e) {
                   echo "Error: $e"
                }

                sh "docker run --name mysql -d -e MYSQL_ALLOW_EMPTY_PASSWORD=yes --rm mysql:latest"
                sh "sleep 10"  // added as mysql takes a little longer than mongo to start
                sh "docker network connect elastest_elastest mysql"
                mysqlIP = sh (
                    script: 'docker inspect --format=\\"{{.NetworkSettings.Networks.elastest_elastest.IPAddress}}\\" mysql',
                    returnStdout: true
                ).trim()
                mysqlIP = mysqlIP.substring(1, mysqlIP.length()-1)
                echo "MySQL container IP=${mysqlIP}"
            }

            stage ("Unit tests"){
                echo ("Starting unit tests...")
                echo "Mongo container IP=${mongoIP}"
                withEnv(["ESM_MONGO_HOST=${mongoIP}", "ET_EDM_MYSQL_HOST=${mysqlIP}"]){
                    echo "Mongo container IP=${mongoIP}"
                    echo "MySQL container IP=${mysqlIP}"
                    sh "tox"
                }
                step([$class: 'JUnitResultArchiver', testResults: '**/nosetests.xml'])
            }

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