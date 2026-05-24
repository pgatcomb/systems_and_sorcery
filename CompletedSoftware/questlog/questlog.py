''' Quest log/journal
The purpose of this is to provide players of a tabletop RPG to access a log of available quests, active quests, and completed
quests that are available in a given TTRPG.
Using StreamLIT, players have access to a simple GUI that consists of three tabs: Active, Available and Completed quests.
There they can click (or tap) on a quest to get more details.  A quest can be marked as active, completed or available by
users of the GUI (no need for a GM facing side of the app).
All quest data is stored in a simple csv file and quests
are populated based on if the prerequisite is met.

quests.csv format
id,name,description,type,prereq,status,rewards,quest_giver,difficulty
slay_gophers,Caddyshack - The Revenging,Farmer Davis is having a Gopher problem and needs the players help to fix this,Side,,Active,credits:50,Farmer Davis,easy
msq1,I Could Make you Care,Now that you're well settled in town the mayor has asked you to dinner,Main,,Available,Mine access Key:1|credits:50,Mayor Quimby,trivial
dungeon1,Come from the Land of Ice and Snow,A local gray pelt den is causing problems that needs to be dealt with,Side,msq1,Available,credits:100|salvage:5,Led Zeppelin,normal

'''

import streamlit as st
import pandas as pd
import os

# Configuration
CSV_FILE = 'quests.csv'

def load_data():
    """Loads quest data from CSV."""
    if not os.path.exists(CSV_FILE):
        st.error(f"Quest file '{CSV_FILE}' not found. Please ensure it exists.")
        return pd.DataFrame(columns=['id', 'name', 'description', 'type', 'prereq', 'status', 'rewards', 'quest_giver', 'difficulty'])
    
    # Read CSV, ensure empty prereqs are treated consistently
    df = pd.read_csv(CSV_FILE)
    df['prereq'] = df['prereq'].fillna('')
    if 'rewards' not in df.columns:
        df['rewards'] = ''
    if 'quest_giver' not in df.columns:
        df['quest_giver'] = 'Unknown'
    if 'difficulty' not in df.columns:
        df['difficulty'] = 'Normal'
    df['rewards'] = df['rewards'].fillna('')
    return df

def save_data(df):
    """Saves quest data to CSV."""
    df.to_csv(CSV_FILE, index=False)

def is_prereq_met(df, prereq_id):
    """Checks if a prerequisite quest is completed."""
    if not prereq_id:
        return True
    
    # Find the prerequisite quest row
    prereq_row = df[df['id'] == prereq_id]
    if prereq_row.empty:
        return False # Prereq quest doesn't exist
    
    return prereq_row.iloc[0]['status'] == 'Completed'

def format_rewards(reward_str):
    """Formats the reward string into a readable list."""
    if not reward_str:
        return "None"
    try:
        items = []
        for part in str(reward_str).split('|'):
            if ':' in part:
                name, qty = part.split(':')
                items.append(f"{qty} {name}")
            else:
                items.append(part)
        return ", ".join(items)
    except:
        return str(reward_str)

def get_difficulty_color(difficulty):
    """Returns the color for a given difficulty."""
    colors = {
        'trivial': 'black',
        'easy': 'blue',
        'normal': 'green',
        'hard': 'gold', # Yellow can be hard to read on white, using Gold/Yellow
        'impossible': 'red'
    }
    return colors.get(str(difficulty).lower(), 'black')

def main():
    st.title("Quest Log")

    # Load Data
    df = load_data()

    # Sorting Controls
    sort_option = st.selectbox("Sort by:", ["Name", "Provider", "Type", "Difficulty"])
    
    if sort_option == "Name":
        df = df.sort_values(by="name")
    elif sort_option == "Provider":
        df = df.sort_values(by="quest_giver")
    elif sort_option == "Type":
        df = df.sort_values(by="type")
    elif sort_option == "Difficulty":
        diff_order = {'trivial': 0, 'easy': 1, 'normal': 2, 'hard': 3, 'impossible': 4}
        df['diff_rank'] = df['difficulty'].str.lower().map(diff_order).fillna(99)
        df = df.sort_values(by="diff_rank")

    # Create Tabs
    tab_active, tab_available, tab_completed = st.tabs(["Active", "Available", "Completed"])

    # --- Active Quests Tab ---
    with tab_active:
        st.header("Active Quests")
        active_quests = df[df['status'] == 'Active']
        
        if active_quests.empty:
            st.info("No active quests.")
        
        for index, row in active_quests.iterrows():
            with st.expander(f"**{row['name']}** - **{row['quest_giver']}** ({row['type']})"):
                st.write(row['description'])
                diff_color = get_difficulty_color(row['difficulty'])
                st.markdown(f"**Difficulty:** <span style='color:{diff_color}'>{row['difficulty']}</span>", unsafe_allow_html=True)
                st.write(f"**Rewards:** {format_rewards(row['rewards'])}")
                col1, col2, col3 = st.columns([1, 1, 3])
                if col1.button("Complete", key=f"comp_{row['id']}"):
                    df.loc[df['id'] == row['id'], 'status'] = 'Completed'
                    save_data(df)
                    st.rerun()
                if col2.button("Abandon", key=f"abn_{row['id']}"):
                    df.loc[df['id'] == row['id'], 'status'] = 'Available'
                    save_data(df)
                    st.rerun()

    # --- Available Quests Tab ---
    with tab_available:
        st.header("Available Quests")
        # Filter: Status is Available AND Prerequisite is met (or empty)
        available_quests = df[df['status'] == 'Available']
        
        count = 0
        for index, row in available_quests.iterrows():
            if is_prereq_met(df, row['prereq']):
                count += 1
                with st.expander(f"**{row['name']}** - **{row['quest_giver']}** ({row['type']})"):
                    st.write(row['description'])
                    diff_color = get_difficulty_color(row['difficulty'])
                    st.markdown(f"**Difficulty:** <span style='color:{diff_color}'>{row['difficulty']}</span>", unsafe_allow_html=True)
                    st.write(f"**Rewards:** {format_rewards(row['rewards'])}")
                    if row['prereq']:
                        st.caption(f"Prerequisite met: {row['prereq']}")
                    
                    if st.button("Accept Quest", key=f"accept_{row['id']}"):
                        df.loc[df['id'] == row['id'], 'status'] = 'Active'
                        save_data(df)
                        st.rerun()
        
        if count == 0:
            st.info("No quests currently available.")

    # --- Completed Quests Tab ---
    with tab_completed:
        st.header("Completed Quests")
        completed_quests = df[df['status'] == 'Completed']
        # Create a display copy to show formatted rewards
        display_df = completed_quests[['name', 'quest_giver', 'description', 'type', 'difficulty', 'rewards']].copy()
        display_df['rewards'] = display_df['rewards'].apply(format_rewards)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()