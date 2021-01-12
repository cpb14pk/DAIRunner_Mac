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
		echo 'Starting DAI Runner...'
            sh 'chmod +x DAIrunner'
            sh './DAIrunner -v testconfig TestConfigIntegration'
        }
    }
}
}
