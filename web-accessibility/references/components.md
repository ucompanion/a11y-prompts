# 컴포넌트별 체크리스트

자주 만드는 UI 컴포넌트마다 꼭 들어가야 할 마크업과 키보드·초점 동작이다. L2·L3 작업에서 탭, 모달 같은 커스텀 컴포넌트를 만들 때 따른다. L1에서는 기준으로 지정하지 않으며 직접 판단해 처리한다.

| 컴포넌트 | 필수 마크업 | 키보드·초점 동작 |
|---|---|---|
| 탭 | `role="tablist"` / `tab` / `tabpanel`, `aria-selected`, `aria-controls` | 좌우 방향키로 탭 이동, 선택된 탭만 `tabindex="0"` |
| 모달 | `role="dialog"`, `aria-modal="true"`, `aria-labelledby`로 제목 연결 | 열리면 모달 안으로 초점 이동, Tab 순환을 모달 안에 가둠, Esc로 닫기, 닫으면 연 버튼으로 초점 복귀 |
| 아코디언 | 제목 `<button aria-expanded aria-controls>`, 패널에 `id` | Enter·Space로 토글, `aria-expanded` 값 갱신 |
| 슬라이드(캐러셀) | 정지·재생, 이전·다음 버튼, 현재 위치("3 / 5") 텍스트 | 자동 재생은 초점·마우스오버 시 멈춤, 숨겨진 슬라이드 안 링크는 초점 제외 |
| 드롭다운 메뉴 | 트리거 `<button aria-expanded aria-haspopup>` | Enter로 열기, Esc로 닫고 트리거로 초점 복귀 |
| 폼 | `<label for>`, `<fieldset>`·`<legend>`로 그룹, `autocomplete` | 오류 시 첫 오류 필드로 초점 이동 또는 `role="alert"`로 안내 |
| 이미지·아이콘 버튼 | `<button>` 안에 `alt` 또는 숨김 텍스트 | 초점 표시 확인 |
| 토스트·알림 | `role="status"`(일반) 또는 `role="alert"`(긴급) | 초점을 뺏지 않음, 충분한 표시 시간 |
| 페이지네이션 | `<nav aria-label="페이지">`, 현재 페이지 `aria-current="page"` | 이전·다음 링크에 텍스트 제공 |
