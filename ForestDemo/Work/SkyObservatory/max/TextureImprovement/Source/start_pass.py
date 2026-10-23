from pathlib import Path
from datetime import datetime,timezone
import json
ROOT=Path(r'D:/github/AstraEffort/ForestDemo/Work/SkyObservatory/max');PASS=ROOT/'TextureImprovement'
for name in ['Source','SourceArt','ImageGen','Evidence','Screenshots']:(PASS/name).mkdir(parents=True,exist_ok=True)
start='2026-10-23T14:00:53.6105607+00:00'
status={'theme':'SkyObservatory','effort':'max','status':'working','started_at_utc':start,'finished_at_utc':None,'elapsed_seconds':0,'baseline_commit':'a96406a9f71b49328e0d70d576bb9ae0660466f7','map':'/Game/Maps/SkyObservatory_max','validation_summary':'Connected-surface UV and fresh image-generated material pass starting','blockers':[]}
(PASS/'STATUS.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
root_status=json.loads((ROOT/'STATUS.json').read_text(encoding='utf-8-sig'));root_status['status']='working';root_status['texture_improvement']=dict(status)
(ROOT/'STATUS.json').write_text(json.dumps(root_status,ensure_ascii=False,indent=2),encoding='utf-8')
report=(ROOT/'RESULT.md').read_text(encoding='utf-8-sig')
report=report.replace('# 하늘섬 천문대 — SkyObservatory / max','# 하늘섬 천문대 — SkyObservatory / max\n\n## 첫 전달본 (커밋 a96406a9f71b49328e0d70d576bb9ae0660466f7)',1)
report+='''

---

## 두 번째 텍스처 품질 패스 — 설계와 구현 계획

사용자의 “텍스쳐 시간들여서 한번더 개선해”, “커밋후 진행해” 지시에 따라 첫 전달본의 커밋과 불변 보관을 확인한 후 시작했다. 첫 전달본의 시간·이미지·소스·검증 기록은 `FirstDelivery/`와 전용 scratch의 `FirstDeliveryContent/`에 보존되며 변경하지 않는다. 별도 시작 UTC는 `2026-10-23T14:00:53.6105607+00:00`이다.

해결할 주요 결함은 모든 삼각형마다 회전·위상이 달라지던 UV 때문에 풀·암석·석벽·돔에 나타난 삼각형 조각무늬다. 연결된 표면을 연속적으로 투영하고, 자연물/석재에는 동일한 미터 스케일의 연속 투영을, 돔과 원통에는 곡면 매핑을, 목재에는 부품 길이 방향 매핑을 사용한다. 표면 대비를 감추는 대신 실제 샘플 좌표의 연속성을 고친다. 100m 범위, 다섯 섬과 모든 형상·배치, 양의 unit actor scale, 카메라와 조명은 보존한다.

청록 금속 도장·옅은 석회암·청보라 암석·따뜻한 목재의 주요 표면 4종을 built-in ImageGen으로 독립 생성한다. 원본은 타일 가능한 정면 알베도이며 글자·그림자·원근을 넣지 않는다. 황동은 저잡음 색상과 금속성/거칠기 차이, 약한 재질 노멀로 정리한다. 신규 원본·프롬프트·계측·검증·스크린샷은 모두 `TextureImprovement/` 아래에 둔다.

- [x] 첫 전달 커밋·보존 위치 확인 및 별도 패스 상태/시간 기록
- [ ] 주요 알베도 4종 생성·검토·프롬프트/원본/시간/해시/용도 기록
- [ ] 삼각형 단위 UV를 연속 곡면·부품 방향 매핑으로 교체하고 밀도·연속성·의도된 seam/overlap 검사
- [ ] 실제 재수출 FBX를 다시 읽어 형상/면 방향/UV를 검사하고 기존 17개 메시·158,816삼각형·2,446닫힌 성분 보존 확인
- [ ] 전용 UE 프로젝트의 재질/텍스처/메시 갱신 후 저장 맵 재로드와 비어 있지 않은 재귀 의존성·실제 배치 자산 대조
- [ ] 같은 카메라 4장과 실제 UE 재질 상세 시점 최소 2장을 캡처하고 첫 전달본과 전후 비교
- [ ] 감독자 시각 검토 후 전용 UE 종료, 소유 경로만 게시·SHA256 대조, 실제 패스 결과와 전후 근거 추가

검증 완료 전 개선 성공을 주장하지 않는다. ImageGen 실패 시 실제 오류를 기록하며 임의 CLI/API 경로로 대체하지 않는다. 기존 실행·검증 스킬을 적용하되 별도 보고서/커밋/다른 경로의 지침은 사용자 지정 소유 범위와 단일 보고서 규칙으로 대체한다.
'''
(ROOT/'RESULT.md').write_text(report,encoding='utf-8')
print(json.dumps(status,indent=2))
