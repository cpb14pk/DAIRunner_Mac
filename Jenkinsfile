

pipeline {
    agent any

    stages {
        stage('Start') {
            steps {
                echo 'Build starting'
            }
        }

    
        stage('Run Tests'){
        steps {
            sh 'chmod +x DAIrunner'
            sh './DAIrunner'
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
