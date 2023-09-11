## hadoop 설치
1. AWS 인스턴스 생성
2. hadoop 계정 생성
3. rsa 페어 생성을 통한 ssh 로그인 보안 설정
4. /etc/ssh/sshd_config 설정 변경을 통한 hadoop 계정 ssh 접속 허용
5. java 설치
6. hadoop 설치 및 환경변수 추가
7. hadoop 환경파일 변경
8. 이미지 복사를 통한 namenode, datanode1, datanode2 추가
9. host 등록
10. hadoop 실행 (start-dfs.sh, start-yarn.sh, jps)
11. port 확인, namenode 50070, secondnode: 8088, 9870