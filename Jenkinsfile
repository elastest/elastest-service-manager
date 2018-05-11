node('docker'){
    stage "Container Prep"
        def mycontainer = docker.image('elastest/ci-docker-compose-py-siblings:latest')
        mycontainer.pull() // make sure we have the latest available from Docker Hub

        mycontainer.inside("-u jenkins -v /var/run/docker.sock:/var/run/docker.sock:rw") {

            git 'https://github.com/elastest/elastest-service-manager'

            stage ("ESM Tests"){
                echo ("Starting unit and integration tests from the tester container...")
                sh "docker-compose -f docker-compose-tester.yml up --build --exit-code-from esm"
                step([$class: 'JUnitResultArchiver', testResults: '**/nosetests.xml'])
            }

            stage "Build ESM Image"
                echo ("building...")
                sh 'docker build -f Dockerfile-esm --build-arg GIT_COMMIT=$(git rev-parse HEAD) --build-arg COMMIT_DATE=$(git log -1 --format=%cd --date=format:%Y-%m-%dT%H:%M:%S) . -t elastest/esm:latest'
                def myimage = docker.image("elastest/esm:latest")

            stage "Publish ESM Image to DockerHub"
                echo ("Publishing as all tests succeeded...")
                withCredentials([[$class: 'UsernamePasswordMultiBinding', credentialsId: 'elastestci-dockerhub',
                usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {
                    sh 'docker login -u "$USERNAME" -p "$PASSWORD"'
                    myimage.push()
                }
        }
}
