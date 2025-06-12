import os
import base64
import markdown as md
import tempfile
from markdown_pdf import MarkdownPdf, Section
from Agents.search_agent import SearchAgent

class ReportGeneratorAgent:
    """
    Agent responsible for generating dermatological diagnosis reports in Markdown and PDF formats,
    including integration of relevant images obtained via SearchAgent.
    """

    @staticmethod
    def generate_report_markdown(final_diagnose: dict) -> str:
        """
        Generate a comprehensive dermatological diagnosis report in Markdown format.

        Args:
            final_diagnose (dict): Dictionary containing diagnosis details including:
                - disease (str): Name of the diagnosed disease.
                - justification (str): Justification for the diagnosis.
                - possible_causes (str): Possible causes of the disease.
                - treatment_and_recommendation (str): Treatment and recommendations.
                - conclusion (str): Final conclusion.
                - differential_diagnosis (dict): Alternative diagnoses with justifications.

        Returns:
            str: Generated report in Markdown format.
        """
        disease = final_diagnose.get("disease", "Unknown Disease")
        justification = final_diagnose.get("justification", "No justification provided.")
        causes = final_diagnose.get("possible_causes", "No causes provided.")
        treatment = final_diagnose.get("treatment_and_recommendation", "No treatment recommendations provided.")
        conclusion = final_diagnose.get("conclusion", "No conclusion provided.")
        differentials = final_diagnose.get("differential_diagnosis", {})

        report_md = f"# Dermatological Diagnosis Report\n\n"
        report_md += "---\n\n"
        report_md += f"## Final Diagnosis: **{disease}**\n\n"
        report_md += "---\n\n"
        report_md += f"### Justification:\n{justification}\n\n"
        report_md += f"### Possible Causes:\n{causes}\n\n"

        # Add relevant images for the primary disease
        search_results = SearchAgent.search_images(disease)
        image_urls = SearchAgent.imgs_url(search_results)
        if image_urls:
            # Include only the first image for brevity
            for url in image_urls[0:1]:
                report_md += f"![{disease}]({url})\n\n"

        report_md += "## Differential Diagnosis\n\n"
        report_md += "---\n\n"
        for key, alt_diag in differentials.items():
            if isinstance(alt_diag, dict):
                alt_disease = alt_diag.get('disease', key)
                alt_justification = alt_diag.get('justification_and_causes', "No justification provided.")
            else:
                alt_disease = key
                alt_justification = alt_diag

            report_md += f"### {alt_disease}\n\n"
            report_md += f"#### Justification & Causes:\n{alt_justification}\n\n"

            # Add images for differential diagnosis if available
            if isinstance(alt_diag, dict):
                alt_search_results = SearchAgent.search_images(alt_disease)
                alt_image_urls = SearchAgent.imgs_url(alt_search_results)
                if alt_image_urls:
                    for url in alt_image_urls[0:1]:
                        report_md += f"![{alt_disease}]({url})\n\n"

        report_md += f"## Treatment & Recommendations\n\n---\n\n{treatment}\n\n"
        report_md += f"## Conclusion\n\n---\n\n{conclusion}\n"

        return report_md

    @staticmethod
    def markdown_to_pdf(md_text: str, filename: str = "dermatology_report.pdf") -> str:
        """
        Convert Markdown text to a styled PDF file using markdown-pdf library.

        Args:
            md_text (str): Markdown text to convert.
            filename (str): Output PDF filename.

        Returns:
            str: Path to the generated PDF file.
        """
        pdf = MarkdownPdf(toc_level=2, optimize=True)

        # Add markdown as a single section (no TOC for title)
        pdf.add_section(Section(md_text, toc=False))

        # Optional: set metadata
        pdf.meta["title"] = "Dermatology Diagnosis Report"
        pdf.meta["author"] = "Derma AI "

        # Save PDF to file
        pdf.save(filename)

        return filename

    