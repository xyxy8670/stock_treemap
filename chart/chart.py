import streamlit as st
import matplotlib.pyplot as plt
import squarify
import numpy as np
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import pandas as pd
from io import BytesIO
import os
import platform

# 페이지 설정
st.set_page_config(page_title="주식 테마 트리맵 생성기", layout="wide")
st.title("주식 테마 트리맵 생성기")


# 로컬 폴더의 Pretendard 폰트 사용 설정
def setup_font():
    try:
        # 사용할 폰트 파일 (Pretendard-Regular.otf)
        font_path = 'Pretendard-Bold.otf'

        # 폰트 파일이 존재하는지 확인
        if os.path.exists(font_path):
            # 폰트 속성 생성
            font_prop = fm.FontProperties(fname=font_path)

            # matplotlib 기본 설정
            plt.rcParams['font.family'] = font_prop.get_name()
            plt.rcParams['axes.unicode_minus'] = False

            st.success("Pretendard 폰트를 성공적으로 불러왔습니다.")
            return font_prop
        else:
            font_files = [f for f in os.listdir('.') if f.startswith('Pretendard-') and f.endswith('.otf')]
            if font_files:
                # 첫 번째 발견된 Pretendard 폰트 사용
                font_path = font_files[0]
                font_prop = fm.FontProperties(fname=font_path)

                # matplotlib 기본 설정
                plt.rcParams['font.family'] = font_prop.get_name()
                plt.rcParams['axes.unicode_minus'] = False

                st.success(f"{font_path} 폰트를 성공적으로 불러왔습니다.")
                return font_prop
            else:
                st.warning("폰트 파일을 찾을 수 없습니다. 기본 폰트를 사용합니다.")
                # 기본 폰트 설정
                system = platform.system()
                if system == 'Darwin':  # macOS
                    plt.rcParams['font.family'] = 'AppleGothic'
                else:
                    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans', 'sans-serif']
                plt.rcParams['axes.unicode_minus'] = False
                return None
    except Exception as e:
        st.warning(f"폰트 설정 중 오류 발생: {str(e)}")
        # 기본 폰트 사용
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
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
# 내부 색상 코드를 입력할 수 있도록 추가 (비워두면 colormap 사용)
custom_color_code = st.sidebar.text_input("내부 색상 코드 (예: #ff0000)", value="")

title_text = st.sidebar.text_input("제목", "테마별 주식 상승률 트리맵")

# 폰트 크기 설정
theme_font_size = st.sidebar.slider("테마명 폰트 크기", 8, 24, 14)
value_font_size = st.sidebar.slider("상승률 폰트 크기", 8, 24, 16)

# 워터마크 옵션
watermark_enabled = st.sidebar.checkbox("워터마크 추가", True)
watermark_text = st.sidebar.text_input("워터마크 텍스트", "플스포")
watermark_opacity = st.sidebar.slider("워터마크 투명도", 0.0, 1.0, 0.3)
watermark_size = st.sidebar.slider("워터마크 크기", 20, 100, 50)

# 현재 데이터 목록 표시 (사이드바에서는 상승률 내림차순으로 정렬)
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

# 메인 영역 - 트리맵 표시
col1, col2 = st.columns([2, 1])

with col1:
    st.header("트리맵 미리보기")

    if st.session_state.theme_data:
        # 트리맵 생성
        fig, ax = plt.subplots(figsize=(10, 6))

        # 데이터 준비
        data = st.session_state.theme_data
        # 입력 순서대로 사용
        labels = list(data.keys())
        values = list(data.values())
        sizes = values

        # 색상 설정
        max_value = max(values) if values else 1
        min_value = min(values) if values else 0
        normalized_values = [
            (val - min_value) / (max_value - min_value) if max_value > min_value else 0.5
            for val in values
        ]

        # 만약 custom_color_code가 입력되었다면 해당 색상을 사용, 아니면 colormap 사용
        if custom_color_code:
            colors = [custom_color_code] * len(normalized_values)
        else:
            cmap = plt.cm.get_cmap(color_option)
            colors = [cmap(0.5 + 0.5 * val) for val in normalized_values]

        # squarify에 들어갈 사이즈 비율 계산
        total = sum(values)
        norm_sizes = [v / total for v in values]

        # 트리맵 생성 (기본 squarify 알고리즘 사용)
        rects = squarify.squarify(norm_sizes, 0, 0, 1, 1)

        # 각 사각형 그리기
        for i, rect in enumerate(rects):
            x, y, dx, dy = rect['x'], rect['y'], rect['dx'], rect['dy']

            # 사각형 배경 색상
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

            # 텍스트 옵션 설정 (테마명)
            text_options = {
                'horizontalalignment': 'center',
                'verticalalignment': 'center',
                'fontsize': theme_font_size,
                'fontweight': 'bold',
                'color': 'white'
            }
            if font_prop is not None:
                text_options['fontproperties'] = font_prop

            # 테마명 텍스트 추가
            ax.text(
                x + dx / 2,
                y + dy / 2 - 0.02,
                f"{labels[i]}",
                **text_options
            )

            # 상승률 텍스트 옵션 설정
            value_options = {
                'horizontalalignment': 'center',
                'verticalalignment': 'center',
                'fontsize': value_font_size,
                'fontweight': 'bold',
                'color': 'white'
            }
            if font_prop is not None:
                value_options['fontproperties'] = font_prop

            # 상승률 텍스트 추가
            ax.text(
                x + dx / 2,
                y + dy / 2 + 0.04,
                f"{values[i]}%",
                **value_options
            )

        # 워터마크 추가
        if watermark_enabled:
            watermark_options = {
                'fontsize': watermark_size,
                'color': 'white',
                'ha': 'center',
                'va': 'center',
                'alpha': watermark_opacity,
                'fontweight': 'bold',
                'rotation': 0
            }
            if font_prop is not None:
                watermark_options['fontproperties'] = font_prop
            fig.text(0.5, 0.5, watermark_text, **watermark_options)

        # 제목 옵션 설정
        title_options = {'fontsize': 18}
        if font_prop is not None:
            title_options['fontproperties'] = font_prop

        # 그래프 설정
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        fig.suptitle(title_text, **title_options)

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
    else:
        st.info("트리맵을 생성하려면 왼쪽 사이드바에서 데이터를 추가하세요.")

with col2:
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