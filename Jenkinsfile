node('docker'){
    stage "Container Prep"
        def mycontainer = docker.image('elastest/ci-docker-compose-py-siblings:latest')
        mycontainer.pull() // make sure we have the latest available from Docker Hub

        mycontainer.inside("-u jenkins -v /var/run/docker.sock:/var/run/docker.sock:rw") {

            git 'https://github.com/elastest/elastest-service-manager'

            stage ("Setup test environment"){
                echo "nothing to do, docker-compose does this for us!"
            }

            stage ("Unit tests"){
                echo ("Starting unit and integration tests from the tester container...")
                sh "docker-compose -f docker-compose-test.yml up --build --exit-code-from tester"
                step([$class: 'JUnitResultArchiver', testResults: '**/nosetests.xml'])
            }

            stage "Build image - Package"
                echo ("building...")
                sh 'docker build -f Dockerfile-esm --build-arg GIT_COMMIT=$(git rev-parse HEAD) --build-arg COMMIT_DATE=$(git log -1 --format=%cd --date=format:%Y-%m-%dT%H:%M:%S) . -t elastest/esm:latest'
                def myimage = docker.image("elastest/esm:latest")

            stage "Publish"
                echo ("Publishing as all tests succeeded...")
                withCredentials([[$class: 'UsernamePasswordMultiBinding', credentialsId: 'elastestci-dockerhub',
                usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {
                    sh 'docker login -u "$USERNAME" -p "$PASSWORD"'
                    myimage.push()
                }
        }
}