from jinja2 import Environment, FileSystemLoader
from abc_ord import a_to_z as ordinal_abc


if __name__ == '__main__':
    # this workflow should be a test

    import worksheet_generator.question_class as question_class
    import worksheet_generator.input_parsers.parse_text as parse_text
    from worksheet_generator.output_generators.pdf_output.abc_ord import a_to_z as ordinal_abc
    env = Environment(
        loader=FileSystemLoader('./PDF_templates')
    )
    template = env.get_template("draft_single_column_pdf.jinja2.template")

    # read test_test_questions
    worksheet_q_list = []
    text_file_name = 'test_text_questions.txt'
    for question_text, answer_choices, solution in parse_text.parse_text_file(text_file_name):
        worksheet_q_list.append(question_class.TextQ(question_text, answer_choices, solution))

    template_vars = {"title": "Test worksheet",
                     "question_list": worksheet_q_list,
                     "ordinal_abc": ordinal_abc}

# render html of these questions

    html_out = template.render(template_vars)

# render pdf from html

    from weasyprint import HTML
    HTML(string=html_out).write_pdf("test_text_worksheet1.pdf")