from GoogleFormsUpdater import createClusters


def pick_topic(choice):
    selected_topics = createClusters()
    
    if not (1 <= choice <= len(selected_topics)):
        raise ValueError(f"Choice must be between 1 and {len(selected_topics)}")
    
    chosen_topic = selected_topics[choice - 1]
    return chosen_topic

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pick a topic based on user choice (1-5)")
    parser.add_argument('--choice', type=int, required=True, help="Choice index (1-5)")
    args = parser.parse_args()

    topic = pick_topic(args.choice)
    print(f"Selected Topic: {topic}")