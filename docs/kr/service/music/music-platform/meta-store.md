# META STORE

### '\*\*년 만 컴백' 신곡, .. 돌아왔다.

메타스토어는 지속적으로 발매되는 앨범을 서비스하기 위한 아티스트, 트랙, 가사, 음원, 비디오와 같은 뮤직 메타 데이터를 CP(Content Provider)사와 연계하여 실시간 적재/가공하는 데이터 파이프라인 + API 플랫폼입니다. &#x20;

![META STORE Architecture](/careers/assets/kr/music-metastore.png)

CP사로부터  메타 데이터를 전송 받는 **뮤직입수서버**(Spring Cloud + Kotlin + K8S)는 해당 데이터에 대해 검증/가공 한 후 **MongoDB**에 데이터를 1차 저장 한 후 **SCDF**(Spring Cloud Data Flow + K8S) **데이터 파이프라인**에 **이벤트**(Kafka)를 전달하여 서비스 구성에 필요한 아티스트/트랙/상품등록/음원적재/비디오적재/싱크가사/노래방채점/네이버검색등록 같은 다양한 프로세스를 수행한 후 메타 데이터를 가공/추출하여 뮤직(바이브+) 서비스 구성에 맞게 2차 적재 처리합니다.&#x20;

![META PIPELINE](/careers/assets/kr/music-scdf-pipeline.png)

적재된 메타 데이터는 메타스토어 **META-API** (Spring Cloud + Kotlin + K8S)를 통해서 **VIBE** 서비스내 모든 컨텐츠에 연계/제공 되어 집니다.

![META-API (+WebSocket)](/careers/assets/kr/music-meta-api-album.png)

또한 **정시오픈 모니터링 시스템**을 통해 적재된 앨범이 실제 발매 되기 전 오픈에 문제가 없는지 다양한 방법으로 점검하여 이상 유무를 판단합니다.

![Open Monitoring](/careers/assets/kr/music-spply-monitoring.png)

**META STORE** = **뮤직입수서버 + 데이터적재파이프라인(SCDF) + 메타API + 정시오픈 모니터링** 를 통합하는 플랫폼으로 국내 서비스를 넘어 글로벌 뮤직 서비스 확장을 위해 표준화된 절차와 프로세스를 정의하여 구현해 가고자 합니다.
