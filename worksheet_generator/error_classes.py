class SolutionUnavailableError(ValueError):
    # log question (esp answer.solution sets) with traceback

    # caller needs to handle if error possible (ie already saved in database questions or self-generated questions
    # should not throw this error if from database etc and maybe shouldn't be caught in that case, as all questions
    # stored in the database should be sanity checked

    pass
