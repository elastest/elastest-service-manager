node('docker'){
    stage "Container Prep"
        def mycontainer = docker.image('elastest/ci-docker-compose-py-siblings:latest')
        mycontainer.pull() // make sure we have the latest available from Docker Hub

        mycontainer.inside("-u jenkins -v /var/run/docker.sock:/var/run/docker.sock:rw") {

            git 'https://github.com/elastest/elastest-service-manager'

            // we split the esm tests in functional areas to minimise resource usage
            stage ("ESM Tests: Core, EPM"){
                echo ("Starting unit and integration tests for core, EMP & AAA from the tester container...")
                withCredentials([string(credentialsId: 'CODECOV_TOKEN', variable: 'CODECOV_TOKEN')]) {
                    sh "docker-compose -f tests/docker/docker-compose-tester-core.yml up --build --exit-code-from esm"
                }
                sh "docker-compose -f tests/docker/docker-compose-tester-core.yml down -v"
                step([$class: 'JUnitResultArchiver', testResults: '**/nosetests.xml'])
            }

            stage ("ESM Tests: Core, EMP"){
                echo ("Starting unit and integration tests for core & EMP from the tester container...")
                withCredentials([string(credentialsId: 'CODECOV_TOKEN', variable: 'CODECOV_TOKEN')]) {
                    sh "docker-compose -f tests/docker/docker-compose-tester-emp.yml up --exit-code-from esm"
                }
                sh "docker-compose -f tests/docker/docker-compose-tester-emp.yml down -v"
                step([$class: 'JUnitResultArchiver', testResults: '**/nosetests.xml'])
            }
            stage ("ESM Tests: Core, AAA(keystone)"){
                echo ("Starting unit and integration tests for core & AAA(keystone) from the tester container...")
                withCredentials([string(credentialsId: 'CODECOV_TOKEN', variable: 'CODECOV_TOKEN')]) {
                    sh "docker-compose -f tests/docker/docker-compose-tester-aaa.yml up --exit-code-from esm"
                }
                sh "docker-compose -f tests/docker/docker-compose-tester-aaa.yml down -v"
                step([$class: 'JUnitResultArchiver', testResults: '**/nosetests.xml'])
            }
            stage "Build ESM Image"
                echo ("building...")
                sh 'docker build --build-arg GIT_COMMIT=$(git rev-parse HEAD) --build-arg COMMIT_DATE=$(git log -1 --format=%cd --date=format:%Y-%m-%dT%H:%M:%S) . -t elastest/esm:latest'
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
