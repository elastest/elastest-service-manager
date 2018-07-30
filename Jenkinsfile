node('docker'){
    stage "Container Prep"
        def mycontainer = docker.image('elastest/ci-docker-compose-py-siblings:latest')
        mycontainer.pull() // make sure we have the latest available from Docker Hub

        mycontainer.inside("-u jenkins -v /var/run/docker.sock:/var/run/docker.sock:rw") {

            git 'https://github.com/elastest/elastest-service-manager'

            // we split the esm tests in functional areas to minimise resource usage
            stage ("ESM Tests: Core, Mongo, EPM"){
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
            stage ("ESM Tests: MySQL"){
                echo ("Starting unit and integration tests for core & MySQL from the tester container...")
                withCredentials([string(credentialsId: 'CODECOV_TOKEN', variable: 'CODECOV_TOKEN')]) {
                    sh "docker-compose -f tests/docker/docker-compose-tester-sql.yml up --exit-code-from esm"
                }
                sh "docker-compose -f tests/docker/docker-compose-tester-sql.yml down -v"
                step([$class: 'JUnitResultArchiver', testResults: '**/nosetests.xml'])
            }
            stage("Build ESM Image"){
                echo ("Building as all tests succeeded...")
                sh 'docker build --build-arg GIT_COMMIT=$(git rev-parse HEAD) --build-arg COMMIT_DATE=$(git log -1 --format=%cd --date=format:%Y-%m-%dT%H:%M:%S) . -t elastest/esm:latest'
            }
            stage ("Publish ESM Image to DockerHub"){
                echo ("Publishing to dockerhub...")
                withCredentials([[$class: 'UsernamePasswordMultiBinding', credentialsId: 'elastestci-dockerhub',
                usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {
                    sh 'docker login -u "$USERNAME" -p "$PASSWORD"'
                    def esm_image = docker.image("elastest/esm:latest")
                    esm_image.push()
                }
            }
            stage('Email results'){
                emailext body: '''<html> <head> <link rel="stylesheet" type="text/css" href="http://fonts.googleapis.com/css?family=Montserrat:400,700%7CLato:300,300italic,400,700,900%7CYesteryear"> </head> <body> <table style="border-spacing: 0px;border-collapse: collapse;"> <tbody> <tr> <td colspan="2">&nbsp;</td> </tr> <tr bgcolor="#666666"> <td style="padding:20px;font-size:1.0em;color:#ffffff;background-color:#666666;font-family:Helvetica,Arial,sans-serif;line-height:1.5em"> <a href="https://ci.elastest.io/jenkins" style=" font-family: Lato, Helvetica, Arial, sans-serif; text-decoration: none; color: #ffffff; font-size: x-large;"> Elastest Jenkins</a> </td> <td align="center"> <a href="https://elastest.io"><img alt="Elastest Community" border="0" src="http://elastest.eu/images/intense/elastest-logo-dark.png"></a> </td> </tr> <tr> <td colspan="2" bgcolor="#FFFFFF" style="padding:0px 20px 20px 20px;font-size:1.0em;color:#333333;background-color:#ffffff;font-family:Helvetica,Arial,sans-serif;line-height:1.5em" valign="top"> <br><br> <p>The result of the ${JOB_NAME} (${BUILD_NUMBER}) has been: <span style="font-family: monospace;">${BUILD_STATUS}</span></p> <br> <p> <strong>You can find more information:: </strong> <ul> <li>Logs: <a href="${BUILD_URL}/console"></a>${BUILD_URL}/console </li> <li>Pipeline: <a href="${BUILD_URL}">${BUILD_URL}</a> </li> </ul> </p> <br> <p> If you have any problem with the CI environment or the Jenkins please contact us <a href="mailtoelastest@naevatec.com" style="color:#ffac2f;text-decoration:bold" target="_blank"><strong>elastest@naevatec.com</strong></a> </p> <br><br> <p style="font-size: small;"><strong>CONFIDENTIALITY NOTICE:</strong><br> The contents of this email message and any attachments are intended solely for the addressee(s)and may contain confidential and/or privileged information and may be legally protected from disclosure. If you are not the intended recipient of this message or their agent, or if this message has been addressed to you in error, please immediately alert the sender by reply email and then delete this message and any attachments. If you are not the intended recipient, you are hereby notified that any use, dissemination, copying, or storage of this message or its attachments is strictly prohibited. </p> </td> </tr> <tr bgcolor="#ffac2f"> </tr> <tr> <td>&nbsp;</td> <td>&nbsp;</td> </tr> </tbody> </table> </body> </html>''',
                replyTo: '${BUILD_USER_EMAIL}',
                subject: '${BUILD_STATUS}: Job ${JOB_NAME} - ${BUILD_NUMBER}',
                to: 'edmo@zhaw.ch'
            }
        }
}
