import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import requests
import io


def setup_font():
    try:
        # GitHub Raw 또는 CDN에서 Pretendard 폰트 파일을 바로 읽어들여 메모리에 저장
        font_url = 'https://github.com/orioncactus/pretendard/raw/main/packages/pretendard-std/dist/web/static/PretendardStd-SemiBold.otf'
        response = requests.get(font_url)
        if response.status_code == 200:
            font_bytes = io.BytesIO(response.content)

            # 폰트 매니저에 등록
            fm.fontManager.addfont(font_bytes)
            font_obj = fm.FontProperties(fname=font_bytes)

            # 폰트 이름 확인
            st.write(f"폰트 이름: {font_obj.get_name()}")

            # matplotlib에 폰트 적용
            plt.rcParams['font.family'] = font_obj.get_name()
            plt.rcParams['axes.unicode_minus'] = False

            return font_obj
        else:
            st.warning(f"폰트 다운로드 실패(상태 코드: {response.status_code})")
            return None
    except Exception as e:
        st.warning(f"폰트 설정 오류: {str(e)}")
        return None


font_prop = setup_font()


# Pretendard 폰트 다운로드 및 설정 (더 명확한 경로 지정)
def setup_font():
    try:
        # 폰트 저장 경로
        font_dir = os.path.join(os.getcwd(), 'fonts')
        os.makedirs(font_dir, exist_ok=True)
        font_path = os.path.join(font_dir, 'PretendardStd-SemiBold.otf')

        # 폰트 파일이 없으면 다운로드
        if not os.path.exists(font_path):
            font_url = 'https://github.com/orioncactus/pretendard/raw/main/packages/pretendard-std/dist/web/static/PretendardStd-SemiBold.otf'

            try:
                response = requests.get(font_url)
                if response.status_code == 200:
                    with open(font_path, 'wb') as f:
                        f.write(response.content)
                    st.success(f"Pretendard 폰트를 다운로드했습니다: {font_path}")
                else:
                    st.warning(f"폰트 다운로드 실패 (상태 코드: {response.status_code}). 시스템 폰트를 사용합니다.")
                    return None
            except Exception as e:
                st.warning(f"폰트 다운로드 오류: {str(e)}")
                return None

        # 폰트 등록 및 적용
        try:
            # 폰트를 matplotlib 캐시에 추가
            fm.fontManager.addfont(font_path)
            # 폰트 매니저에 등록
            font_obj = fm.FontProperties(fname=font_path)

            # 폰트 속성 확인
            st.text(f"폰트 이름: {font_obj.get_name()}")
            st.text(f"폰트 패밀리: {font_obj.get_family()}")

            # matplotlib에 폰트 설정 (폰트 이름 사용)
            plt.rcParams['font.family'] = font_obj.get_name()
            plt.rcParams['axes.unicode_minus'] = False

            return font_obj
        except Exception as e:
            st.warning(f"폰트 등록 오류: {str(e)}")
            return None
    except Exception as e:
        st.warning(f"폰트 설정 오류: {str(e)}")
        return None


# 폰트 설정 적용
font_prop = setup_font()

# 사이드바 - 데이터 입력
st.sidebar.header("테마 데이터 입력")
theme_name = st.sidebar.text_input("테마 이름")
theme_value = st.sidebar.number_input("상승률(%)", min_value=0.0, format="%.2f")

# 세션 상태 초기화
if 'theme_data' not in st.session_state:
    st.session_state.theme_data = {}

# 데이터 추가 버튼
if st.sidebar.button("데이터 추가"):
    if theme_name and theme_value:
        st.session_state.theme_data[theme_name] = theme_value
        st.sidebar.success(f"테마 '{theme_name}'이(가) {theme_value}% 상승률로 추가되었습니다.")

# 시각화 옵션
st.sidebar.header("시각화 옵션")
color_option = st.sidebar.selectbox("색상 계열", ["Reds", "Greens", "Blues", "Purples", "Oranges"])
title_text = st.sidebar.text_input("제목", "테마별 주식 상승률 트리맵")

# 폰트 크기 설정
theme_font_size = st.sidebar.slider("테마명 폰트 크기", 8, 24, 14)
value_font_size = st.sidebar.slider("상승률 폰트 크기", 8, 24, 16)

# 워터마크 옵션
watermark_enabled = st.sidebar.checkbox("워터마크 추가", True)
watermark_text = st.sidebar.text_input("워터마크 텍스트", "플스포")
watermark_opacity = st.sidebar.slider("워터마크 투명도", 0.0, 1.0, 0.3)
watermark_size = st.sidebar.slider("워터마크 크기", 20, 100, 50)

# 현재 데이터 목록 표시
st.sidebar.header("현재 데이터")
if st.session_state.theme_data:
    data_df = pd.DataFrame(
        {'테마': list(st.session_state.theme_data.keys()),
         '상승률(%)': list(st.session_state.theme_data.values())}
    )
    st.sidebar.dataframe(data_df.sort_values('상승률(%)', ascending=False))

# 데이터 삭제 옵션
if st.session_state.theme_data:
    delete_option = st.sidebar.selectbox("삭제할 테마 선택", list(st.session_state.theme_data.keys()))
    if st.sidebar.button("선택한 테마 삭제"):
        del st.session_state.theme_data[delete_option]
        st.sidebar.success(f"테마 '{delete_option}'이(가) 삭제되었습니다.")

if st.sidebar.button("모든 데이터 삭제"):
    st.session_state.theme_data = {}
    st.sidebar.success("모든 데이터가 삭제되었습니다.")

# 메인 영역 - 샘플 데이터 버튼 및 트리맵 표시
st.header("샘플 데이터")
if st.button("샘플 데이터 불러오기"):
    st.session_state.theme_data = {
        "반도체 재료/부품": 12.91,
        "화장품": 12.05,
        "제약/바이오": 10.53,
        "반도체 장비": 10.27,
        "우주항공": 9.13,
        "방산": 9.12,
        "AI(인공지능)": 9.04,
        "AI(엔비디아)": 8.99,
        "음식료": 8.97,
        "태양광": 8.73,
        "소매유통": 8.47,
        "이재명": 8.26
    }
    st.success("샘플 데이터가 로드되었습니다.")

st.header("트리맵 미리보기")

if st.session_state.theme_data:
    try:
        # 트리맵 생성
        fig, ax = plt.subplots(figsize=(10, 6))

        # 데이터를 상승률 기준으로 내림차순 정렬
        sorted_data = sorted(st.session_state.theme_data.items(), key=lambda x: x[1], reverse=True)
        labels = [item[0] for item in sorted_data]
        values = [item[1] for item in sorted_data]
        sizes = values

        # 색상 설정
        max_value = max(values) if values else 1
        min_value = min(values) if values else 0
        normalized_values = [(val - min_value) / (max_value - min_value) if max_value > min_value else 0.5 for val in
                             values]

        # 색상 맵 선택
        cmap = plt.cm.get_cmap(color_option)
        colors = [cmap(0.5 + 0.5 * val) for val in normalized_values]

        # 트리맵 생성
        if values:  # 값이 있을 때만 처리
            norm_sizes = [size / sum(sizes) for size in sizes]
            rects = squarify.squarify(norm_sizes, 0, 0, 1, 1)

            # 각 사각형 그리기
            for i, rect in enumerate(rects):
                x, y, dx, dy = rect['x'], rect['y'], rect['dx'], rect['dy']

                # 배경 색상 사각형
                ax.add_patch(
                    patches.Rectangle(
                        (x, y),
                        dx, dy,
                        facecolor=colors[i],
                        edgecolor='white',
                        linewidth=2,
                        alpha=0.8
                    )
                )

                # 텍스트 추가 (테마명과 상승률을 직접 지정)
                if font_prop is not None:
                    # 폰트 속성을 사용하여 텍스트 추가
                    ax.text(
                        x + dx / 2,
                        y + dy / 2 - 0.02,
                        f"{labels[i]}",
                        fontproperties=font_prop,
                        horizontalalignment='center',
                        verticalalignment='center',
                        fontsize=theme_font_size,
                        fontweight='bold',
                        color='white'
                    )

                    ax.text(
                        x + dx / 2,
                        y + dy / 2 + 0.04,
                        f"{values[i]}%",
                        fontproperties=font_prop,
                        horizontalalignment='center',
                        verticalalignment='center',
                        fontsize=value_font_size,
                        fontweight='bold',
                        color='white'
                    )
                else:
                    # 기본 폰트로 텍스트 추가
                    ax.text(
                        x + dx / 2,
                        y + dy / 2 - 0.02,
                        f"{labels[i]}",
                        horizontalalignment='center',
                        verticalalignment='center',
                        fontsize=theme_font_size,
                        fontweight='bold',
                        color='white'
                    )

                    ax.text(
                        x + dx / 2,
                        y + dy / 2 + 0.04,
                        f"{values[i]}%",
                        horizontalalignment='center',
                        verticalalignment='center',
                        fontsize=value_font_size,
                        fontweight='bold',
                        color='white'
                    )

            # 워터마크 추가
            if watermark_enabled:
                if font_prop is not None:
                    fig.text(0.5, 0.5, watermark_text,
                             fontproperties=font_prop,
                             fontsize=watermark_size,
                             color='white',
                             ha='center',
                             va='center',
                             alpha=watermark_opacity,
                             fontweight='bold',
                             rotation=0)
                else:
                    fig.text(0.5, 0.5, watermark_text,
                             fontsize=watermark_size,
                             color='white',
                             ha='center',
                             va='center',
                             alpha=watermark_opacity,
                             fontweight='bold',
                             rotation=0)

        # 제목 추가
        if font_prop is not None:
            fig.suptitle(title_text, fontproperties=font_prop, fontsize=18)
        else:
            fig.suptitle(title_text, fontsize=18)

        # 그래프 설정
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # 그래프 표시
        st.pyplot(fig)

        # 다운로드 버튼
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
        st.download_button(
            label="트리맵 이미지 다운로드",
            data=buf.getvalue(),
            file_name="treemap.png",
            mime="image/png"
        )
    except Exception as e:
        st.error(f"트리맵 생성 중 오류 발생: {str(e)}")
        st.text("오류 상세 정보:")
        st.exception(e)

        # 폰트 없이 기본 방식으로 재시도
        try:
            st.warning("기본 설정으로 다시 시도합니다...")
            fig, ax = plt.subplots(figsize=(10, 6))
            sorted_data = sorted(st.session_state.theme_data.items(), key=lambda x: x[1], reverse=True)
            labels = [item[0] for item in sorted_data]
            values = [item[1] for item in sorted_data]

            squarify.plot(sizes=values, label=[f"{l}\n{v}%" for l, v in zip(labels, values)],
                          alpha=.8, color=plt.cm.get_cmap(color_option)(np.linspace(0.4, 0.8, len(values))), ax=ax)

            ax.axis('off')
            plt.title(title_text, fontsize=18)
            st.pyplot(fig)
        except Exception as e2:
            st.error(f"대체 트리맵 생성 중에도 오류 발생: {str(e2)}")
else:
    st.info("트리맵을 생성하려면 데이터를 추가하거나 샘플 데이터를 불러오세요.")