from apollo import services


def update_participant_completion_rating(participant):
    forms = services.forms.find(form_type='CHECKLIST')
    submissions = services.submissions.find(
        contributor=participant,
        form__in=forms,
        submission_type='O'
    )

    numerator = 0
    denominator = 0
    completion_map = {
        'Missing': 0,
        'Partial': 1,
        'Complete': 2,
        'Conflict': 2  # TODO: find a better way to compute the ratings
    }

    if submissions.count() == 0:
        participant.completion_rating = 1
    else:
        for submission in submissions:
            completion_values = [
                completion_map[i] for i in
                submission.completion.values()
            ]
            denominator += len(submission.form.groups) * 2.0
            numerator += sum(completion_values)

        try:
            participant.completion_rating = (numerator / denominator)
        except ZeroDivisionError:
            # this should never happen
            participant.completion_rating = 1
    participant.save()
