import streamlit as st


def show_character_avatar(character, character_profiles):
    st.image(
        character_profiles[character]["image_url"],
        caption=character,
        use_container_width=True,
    )
