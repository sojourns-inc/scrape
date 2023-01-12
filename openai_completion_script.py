import argparse
import os
import openai
from time import sleep
from datetime import datetime

# Init openai/gpt
openai.api_key = os.getenv("OPENAI_API_KEY")
# Init cmd line parser
parser = argparse.ArgumentParser(description="Report analyzer.")
# Init argument to cmd line parser
parser.add_argument("file_name", type=str, help="File name")


class TripReportAnalyzer(object):
    """
    This function tests the completion API of the OpenAI/GPT model.
    The function takes in a list of training data, and tests the model's ability to predict the presence of an effect.
    The training data is a list of strings, where each string is a report.
    Each report is a string of the following format:
    <report number>
    <report body>
    <effect name> - <presence decision>
    <effect name> - <presence decision>
    <effect name> - <presence decision>
    """
    model = "text-davinci-003"  # OpenAI NLP model name
    test_corpus = None  # Name of file with reports, to be set by the user
    prompt_prefix = "Decide whether an experience report references"

    def __init__(self, file_name):
        self.test_corpus = file_name
        print(self.test_corpus)

    def test_completion_api(self):
        prompt = (
            lambda e: f'{self.prompt_prefix} "{e.lower()}":'
        )  # Prompt for completion
        with open("training.txt", "r") as file:
            data = file.read().split("\n\n")
            for report_raw in data:
                report_tokens = report_raw.split("\n")
                if len(report_tokens) < 5:
                    continue

                # We extract the report text and the effect name
                report_number = report_tokens[0].split(" ")[1]
                report_body = report_tokens[1]
                report_effect_presence = report_tokens[2:]
                for presence_decision_line in report_effect_presence:
                    effect_decision_name_pair = presence_decision_line.split(" - ")

                    if len(effect_decision_name_pair) < 2:
                        print(
                            f"Faulty string in training data: {presence_decision_line}\nskipping..."
                        )

                    # ground_truth_decision = effect_decision_name_pair[0]
                    effect_name = effect_decision_name_pair[1]

                    sleep(
                        2
                    )  # openai/gpt requires a "cooldown" interval if requests are made in rapid succession
                    test_decision_object = openai.Completion.create(
                        model=self.model,
                        prompt=f"{prompt(effect_name)}\n\n{report_body}\n",
                        temperature=0,
                        max_tokens=2122,
                        top_p=1,
                        frequency_penalty=0.5,
                        presence_penalty=0,
                    )

                    # Openai/gpt will respond in a full sentence.
                    # The actual "yes" or "no" response within the sentence, must be extracted
                    test_decision = test_decision_object["choices"][0]["text"]
                    test_decision_label = None
                    if "No, " in test_decision:
                        test_decision_label = "A"
                    elif "Yes, " in test_decision:
                        test_decision_label = "P"
                    else:
                        print(f"Unexpected decision response: {test_decision}")
                        continue

                    print(
                        f"Report {report_number} : {test_decision_label} - {effect_name}"
                    )


if __name__ == "__main__":
    args = parser.parse_args()
    file_name = args.file_name  # get file name

    t = TripReportAnalyzer(file_name=file_name)
    t.test_completion_api()
