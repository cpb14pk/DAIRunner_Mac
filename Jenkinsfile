

pipeline {
    agent any

    stages {
        stage('Start') {
            steps {
                echo 'Build starting'
            }
        }
        
    stage('Checkout') {
    steps {
        git branch: 'JenkinsBuild/TEST-12', url: 'https://github.com/cpb14pk/EggplantRepo.git'
    }
    }

    
        stage('Run Tests'){
        steps {
            sh '/Applications/Eggplant.app/Contents/MacOS/runscript GeniusModel.suite/Scripts/GeniusEx1.script -CommandLineOutput yes'
        }
    }
    
        stage('Build') {
        steps {
            echo 'Building...'
   }
        post {
            always {
                jiraSendBuildInfo site: 'eggplant-tc-test-env.atlassian.net'
       }
   }
}
}
}
