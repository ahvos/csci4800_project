import os
import requests
import gradio as gr
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from sklearn.preprocessing import MinMaxScaler
from final_model import preprocess_data, recommend_songs, model

os.environ["OPENAI_API_KEY"] = "your_openai_api_key_here"
FLASK_SERVER_URL = "http://127.0.0.1:5000"

llm = ChatOpenAI(model="gpt-4", temperature=0.7)
memory = []

spotify_df, X, Y = preprocess_data()
features = X.reshape(-1, X.shape[2])
sequence_length = 10

def generate_song_recommendations():
    print("Generating song recommendations...")
    
    sequence = X[0].reshape(1, sequence_length, X.shape[2])
    track_ids = recommend_songs(model, features, spotify_df, sequence)
    
    recommended_songs = []
    for track_id in track_ids:
        try:
            song_details = spotify_df.loc[spotify_df['track_id'] == track_id].iloc[0]
            recommended_songs.append(f"{song_details['track_name']} by {song_details['artists']}")
        except Exception as e:
            print(f"Error fetching song details for {track_id}: {e}")
    return recommended_songs, track_ids


def chatbot(user_input):
    print(f"User Input: {user_input}")
    try:
        if "recommend songs" in user_input.lower():
            recommended_songs, track_ids = generate_song_recommendations()

            if not recommended_songs:
                return "Bot: I couldn't generate song recommendations. Please try again."

            song_list = "\n".join(recommended_songs)
            bot_response = f"Bot: Here are some songs you might like:\n{song_list}\n\n"
            bot_response += "Bot: Do you want to save these songs to Spotify? (yes/no):"
            memory.append({"track_ids": track_ids})
            return bot_response

        elif user_input.strip().lower() in ["yes", "no"]:
            if not memory or "track_ids" not in memory[-1]:
                return "Bot: I couldn't find any tracks to save. Please request recommendations first."

            track_ids = memory[-1]["track_ids"]
            if user_input.strip().lower() == "yes":
                api_url = f"{FLASK_SERVER_URL}/generate_playlist"
                response = requests.get(api_url, params={"track_ids": ",".join(track_ids)})

                if response.status_code == 200:
                    return "Bot: Playlist saved successfully!"
                else:
                    error_message = response.json().get("error", "Unknown error")
                    return f"Bot: Failed to save playlist: {error_message}"
            else:
                return "Bot: Got it! Let me know if you want more recommendations."

        else:
            print("Processing natural language response...")
            memory.append(HumanMessage(content=user_input))
            assistant_message = llm.generate([HumanMessage(content=user_input)])
            memory.append(assistant_message.generations[0].text)
            return assistant_message.generations[0].text
    except Exception as e:
        print(f"Error: {str(e)}")
        return f"Error: {str(e)}"

demo = gr.Interface(fn=chatbot, inputs="text", outputs="text", title="Spotify Playlist Generator")
recommended_songs, track_ids = generate_song_recommendations()

if __name__ == "__main__":
    demo.launch(debug=True)
