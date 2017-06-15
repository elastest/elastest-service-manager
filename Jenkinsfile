node('docker'){
    stage "Container Prep"
        
        echo("the node is up")
        def mycontainer = docker.image('dizz/py-d-in-d:latest')
        mycontainer.pull() // make sure we have the latest available from Docker Hub
        
        mycontainer.inside("-u jenkins -v /var/run/docker.sock:/var/run/docker.sock:rw") {

            git 'https://github.com/elastest/elastest-service-manager'
            
            stage "Unit tests"
                echo ("Starting unit tests...")
                sh 'ls -l'
                sh 'source /emv/bin/activate'
                sh 'cd elastest-service-manager'
                sh 'tox'

            stage "Build image - Package"
                echo ("building... maybe use packer.io to build both container and VM images?")
                //need to be corrected to the organization because at the moment elastestci can't create new repositories in the organization
                def myimage = docker.build "elastest/elastest-service-manager"
                    
            //stage "Run image"
            //    echo "Run the image... run it as a target of integration tests"
            //    myimage.run()

            //stage "Integration tests"
            //    echo ("Starting unit tests...")
            //    echo ("No tests yet")

            // stage "Publish"
            //     echo ("Publishing as all tests succeeded...")
            //     //this is work arround as withDockerRegistry is not working properly 
            //     withCredentials([[$class: 'UsernamePasswordMultiBinding', credentialsId: 'elastestci-dockerhub',
            //     usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']]) {
            //         sh 'docker login -u "$USERNAME" -p "$PASSWORD"'
            //         myimage.push()
            //     }
        }
}