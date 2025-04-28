import sqlite3
import json
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize

from google.oauth2 import service_account
from googleapiclient.discovery import build

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os


def createClusters(num_topics):
    conn = sqlite3.connect('database/autonews.db')
    cursor = conn.cursor()

    cursor.execute('SELECT title, embedding FROM articles WHERE embedding IS NOT NULL')
    rows = cursor.fetchall()

    titles = []
    embeddings = []

    for row in rows:
        titles.append(row[0])
        embeddings.append(json.loads(row[1]))

    embeddings = np.array(embeddings)
    embeddings = normalize(embeddings)

    oversample_clusters = num_topics * 3
    kmeans = KMeans(n_clusters=oversample_clusters, random_state=42)
    kmeans.fit(embeddings)

    labels = kmeans.labels_
    centers = kmeans.cluster_centers_

    cluster_density = {}
    for label in labels:
        cluster_density[label] = cluster_density.get(label, 0) + 1

    sorted_clusters = sorted(cluster_density.items(), key=lambda x: x[1], reverse=True)

    selected_cluster_ids = [cluster_id for cluster_id, count in sorted_clusters[:num_topics]] # for num_topics topics

    selected_topics = []

    for cluster_id in selected_cluster_ids:
        cluster_points = np.where(labels == cluster_id)[0]
        center = centers[cluster_id]
        
        best_idx = cluster_points[np.argmin([
            np.linalg.norm(embeddings[i] - center) for i in cluster_points
        ])]
        
        selected_topics.append(titles[best_idx])

    print(f"Top {num_topics} Topics for Voting:")
    for idx, topic in enumerate(selected_topics, start=1):
        print(f"{idx}. {topic}")
    print()

    conn.close()

    return selected_topics

def getQuestionId(service, FORM_ID):
    form = service.forms().get(formId=FORM_ID).execute()

    for item in form.get('items', []):
        print(f"Title: {item['title']}")
        print(f"Question ID: {item['questionItem']['question']['questionId']}")
        print('-' * 40)

def authenticate():
    SCOPES = ['https://www.googleapis.com/auth/forms.body']

    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'google_forms_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('forms', 'v1', credentials=creds)
    return service

def main():

    selected_topics = createClusters(num_topics=3)

    FORM_ID = '1FAIpQLSeqjQjpTtSPAQrdndN4qKfnz6bkgurGfYtLcN4WyiT3No_1HA'
    QUESTION_ID = 'your-question-id-here'

    service = authenticate()

    getQuestionId(service, FORM_ID)

    update_request = {
        "requests": [
            {
                "updateItem": {
                    "itemId": QUESTION_ID,
                    "questionItem": {
                        "question": {
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [{"value": topic} for topic in selected_topics],
                                "shuffle": False
                            }
                        }
                    },
                    "updateMask": "question.choiceQuestion.options"
                }
            }
        ]
    }

    response = service.forms().batchUpdate(formId=FORM_ID, body=update_request).execute()
    print('Google Form updated successfully.')
