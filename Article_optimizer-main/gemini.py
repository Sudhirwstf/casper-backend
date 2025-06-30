import os
from dotenv import load_dotenv
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set. Please check your .env file or environment variables.")

# Initialize client with the API key
client = genai.Client(api_key=api_key)

model_id = "gemini-2.0-flash"

google_search_tool = Tool(
    google_search=GoogleSearch()
)

try:
    response = client.models.generate_content(
        model=model_id,
        contents="""


THIS IS THE DATA :Reinstating Practice: Evaluating the Judicial Entry Framework in India and Comparative Jurisdictions
The Supreme Court of India reinstated a 3-year legal practice requirement for entry-level judicial posts, emphasizing the need for real-world experience to enhance judicial competence. This aligns India with common law traditions, prioritizing practical wisdom.

Anish Sinha
Anish Sinha
May 20, 2025 • 7 min read
 

Introduction
Today (May 20, 2025) the Supreme Court of India pronounced a landmark ruling, reinstating the requirement of a minimum of three years of legal practice as a prerequisite for appointment to entry-level judicial posts such as Civil Judge (Junior Division). The Court observed that permitting fresh law graduates to enter the judiciary without any real-world legal experience had proven to be a flawed policy, negatively impacting judicial efficiency and public trust in the justice system. This reinstatement marks a return to the earlier rule, which had been relaxed in 2002 based on recommendations by the Shetty Commission.

The significance of this ruling extends beyond recruitment logistics and it reflects the judiciary's institutional self-correction and an acknowledgment of the vital role courtroom experience plays in shaping competent judges. The decision has been widely welcomed by High Courts across India, with only a few dissenting states such as Sikkim and Chhattisgarh maintaining that such a requirement is unnecessary.

Historical Evolution of Practice Requirement in India
Before 2002, most Indian states mandated that candidates aspiring for lower judicial services should have a minimum of three years of legal practice. This requirement was rooted in the belief that judges must possess firsthand experience in court procedure, client interactions, and legal strategy before being entrusted with adjudicating matters that often pertain to life, liberty, and property. In 1993, in the original All India Judges Association case, the Supreme Court itself endorsed this perspective and directed states to amend rules to require three years of advocacy experience for judicial service aspirants[1].

However, in 2002, the Supreme Court revised its stance. Citing the recommendations of the Shetty Commission and the difficulty in attracting bright young minds to the judiciary, the Court allowed fresh law graduates to compete for judicial posts. It opined that proper training of one to two years could compensate for lack of practice, thus paving the way for direct recruitment from law schools[2]. This was intended to strengthen the judicial cadre and streamline the recruitment process, but over time, practical challenges emerged.

Empirical feedback from the High Courts suggested that fresh law graduates often lacked the confidence, maturity, and contextual understanding required for courtroom decision-making. Despite pre-service training programs, newly recruited judges frequently struggled with procedural nuances and stakeholder management. As a result, several High Courts and judicial officers began lobbying for the reinstatement of the earlier rule mandating practical experience before appointment.

The May 2025 decision thus represents not a policy reversal, but a course correction informed by nearly two decades of experience. It reinstates the importance of lived legal experience as an essential component of judicial competence and institutional integrity. Moreover, it recognizes that adjudication is not merely an intellectual exercise, but a socially embedded practice requiring interaction, observation, and empathy developed through practice.

 Global Comparative Frameworks
Judicial appointment systems vary widely across jurisdictions, reflecting each country’s historical, political, and legal traditions. In common law jurisdictions such as the United Kingdom, Australia, and the United States, a strong emphasis is placed on prior legal practice. For example, in the UK, to be appointed as a Deputy District Judge or Recorder, a candidate must have at least five to seven years of post-qualification experience as a solicitor or barrister[3]. The Judicial Appointments Commission ensures that appointees possess not just academic knowledge but demonstrable legal acumen.

Australia follows a similar pattern. Judicial appointments, particularly in superior courts, are generally made from the ranks of seasoned advocates and senior counsel with significant litigation experience. The Australian system values a candidate’s track record in advocacy, legal writing, and ethical conduct. Though there is no statutory requirement of minimum years in all cases, in practice, appointees typically have over a decade of courtroom experience.

In the United States, state-level judges are often elected or appointed, and while formal requirements vary, successful candidates typically possess many years of legal practice. Federal judges are nominated by the President and confirmed by the Senate, often after long legal or judicial careers. The U.S. model highly values experience, considering it essential to maintaining judicial independence and practical wisdom.

By contrast, civil law countries such as Germany, France, and Japan adopt an institutional training approach. In Germany, students undergo two rigorous state examinations and a two-year legal clerkship (Referendariat) before qualifying for the judiciary[4]. Judges are selected early and trained professionally. Similarly, in France, students take competitive exams to enter the École nationale de la magistrature (ENM), where they receive specialized judicial training. Japan combines bar qualification with mandatory post-bar training at the Legal Training and Research Institute. These systems reflect confidence in structured pedagogy over courtroom experience[5].

India’s reinstated rule now aligns more closely with the common law tradition, placing value on experiential learning over exclusive reliance on pre-service training. This move implicitly questions the sufficiency of classroom knowledge and recognizes that exposure to actual legal practice inculcates decision-making ability, emotional intelligence, and procedural familiarity.

Juristic Perspectives on Legal Experience and Judicial Competence
Several jurists and legal philosophers have underscored the value of experience in shaping judicial temperament and competence. Roscoe Pound argued that "judges must not only know the law, but understand the spirit in which the law operates"[6]. Such understanding is rarely acquired solely through academic learning; it evolves through observation, practice, and interaction within the legal system.

Justice V.R. Krishna Iyer, one of India’s most visionary judges, consistently advocated for socially sensitive and experience-informed judging. In his writings, he stressed that judicial decisions must be informed by the "felt necessities" of the people, which can only be perceived by those who have engaged with the legal system at the grassroots level[7]. A judge, he argued, must be more than a "syllogistic technician"; he must be a socially conscious adjudicator.

In the 2025 decision, the Supreme Court reiterated similar sentiments. The bench emphasized that fresh graduates lack the maturity and contextual understanding that comes from legal practice. Amicus Curiae Siddharth Bhatnagar pointed out the growing trend of nominal practice, where aspirants merely sign vakalatnamas for formality. The Court sought to curb this by requiring certification from a ten-year standing advocate and judicial endorsement, thereby filtering out insincere claims of practice[8].

The ruling also incorporates a degree of flexibility. Time spent working as a law clerk will now count toward the three-year practice requirement. This acknowledges the diverse ways legal experience can be acquired without diluting the core principle that adjudicatory authority must be grounded in lived legal understanding. The Court’s approach reflects a balanced recognition of both formal criteria and qualitative assessment.

Bridging the Bar–Bench Divide: Mentorship, Monitoring, and Modernization
The reinstatement of the practice requirement is not merely a procedural reform but essentially it calls for a deeper integration between the Bar and the Bench. In the current legal ecosystem, young lawyers often face a fragmented path marked by lack of direction, inadequate support systems, and minimal interaction with the judiciary. Bridging this divide requires a comprehensive strategy focused on mentorship, monitoring, and modernization.

First, a formalized mentorship framework under the Bar Council and High Courts can transform early practice into a rich training ground. Pairing junior advocates with experienced seniors can foster skills, discipline, and exposure to diverse areas of law. Such mentoring programs have found success in jurisdictions like Singapore and the UK, where structured pupilage or shadowing systems ensure hands-on legal learning[9].

Second, institutional monitoring of early legal practice is essential. Bar Councils must go beyond mere enrollment statistics and create mechanisms to track actual courtroom exposure, filings, and appearances. Regular assessments, certifications, or practice logs can ensure that legal experience is genuine and not merely nominal.

Third, modernization through digital integration and structured continuing legal education (CLE) can enhance the quality of both advocates and aspirants. Online platforms for filing, tracking case progress, and accessing legal resources can reduce friction and promote competence. CLE modules tailored for aspiring judges can bridge the knowledge-practice gap and standardize learning outcomes across regions[10].

Together, these initiatives can convert the practice requirement from a gatekeeping measure into a developmental opportunity. By supporting young advocates with clear pathways, the judiciary can enhance diversity, quality, and readiness—ensuring that future judges emerge not just qualified, but truly prepared to serve.

Policy Implications and Critique
The Supreme Court’s ruling has significant implications for judicial recruitment, legal education, and access to justice. By making prior practice mandatory, it potentially filters out candidates who lack real-world exposure. This is likely to enhance the quality of judgments, reduce procedural errors, and increase public confidence in the judiciary. However, it may also narrow the pool of candidates and delay the entry of young, talented minds into the judicial system.

One concern is that aspirants from underprivileged backgrounds, who rely on early entry into government service for financial stability, may now be disadvantaged. Legal practice, especially in initial years, is often unpaid or poorly compensated. To address this, Bar Councils and State Governments must consider providing stipends or apprenticeship schemes for junior advocates, thereby democratizing access to the Bench without compromising on quality.

The Court’s provision to count law clerkships and provisional enrollment from the first day is a welcome move in this regard. It recognizes that structured mentorship and judicial exposure, even outside conventional advocacy, contribute meaningfully to the aspirant’s development. Such inclusive provisions ensure that the practice requirement does not become a class barrier.

Additionally, this judgment may prompt reforms in legal education and bar council regulation. Law schools may enhance clinical legal education and court internship programs, while bar councils could strengthen monitoring of junior advocacy to ensure meaningful engagement. The judiciary, bar, and academia must collaborate to build a robust pipeline of future judges who are not only knowledgeable but also judicially mature.

Conclusion
The reinstatement of the minimum practice requirement represents a thoughtful recalibration of judicial recruitment in India. It is not a retreat from inclusivity but a stride toward quality, integrity, and institutional trust. Comparative models show that while civil law countries rely on rigorous judicial training, common law jurisdictions prefer judges seasoned through courtroom experience. India, given its adversarial system and diverse legal landscape, arguably needs the latter.

The judgment affirms that a judge’s role is not merely to apply law but to dispense justice in context. This cannot be accomplished through academic preparation alone. Lived experience, legal practice, and ethical engagement with the legal process are indispensable ingredients of judicial competence. As India aspires to deliver swift, efficient, and equitable justice, the decision to restore the three-year practice rule is a step in the right direction and a step grounded in experience, endorsed by precedent, and guided by wisdom.

[1] All India Judges Association v. Union of India, (1993) 4 SCC 288, at p. 314.

[2] All India Judges Association v. Union of India, (2002) 4 SCC 247.

[3] UK Judiciary, "Becoming a Judge," available at https://www.judiciary.uk/about-the-judiciary/judges-training-selection/becoming-a-judge

[4] https://service.rlp.de/en/detail?areaId=&pstId=231525137&ouId=

[5] M. Bussani and U. Mattei, The Cambridge Companion to Comparative Law (Cambridge University Press, 2012) 115.

[6] Roscoe Pound, Interpretations of Legal History (Harvard University Press, 1923) 1.

[7] V.R. Krishna Iyer, Law and the People (Delhi Law House, 1982) 64.

[8] Supreme Court of India, Judgment dated May 20, 2025 in All India Judges Association v. Union of India (unreported).

[9] Singapore Academy of Law, "Practice Training Contract Guidelines," available at https://www.sal.org.sg (last accessed May 19, 2025).

[10] American Bar Association, "CLE Requirements by State," available at https://www.americanbar.org (last accessed May 19, 2025).



FOR THIS article  I WANT YOU TO FIND related and associated INSTAGRAM IDS/USER HANDLE, JUST GIVE ME WORKING ID OF THEM  WITH THIS @



""",
        config=GenerateContentConfig(
            tools=[google_search_tool],
            response_modalities=["TEXT"],
        )
    )

    # Print the response content
    print("Response:")
    print("-" * 500)
    for part in response.candidates[0].content.parts:
        if hasattr(part, 'text') and part.text:
            print(part.text)

    # Print grounding metadata if available
    if (hasattr(response.candidates[0], 'grounding_metadata') and 
        response.candidates[0].grounding_metadata and
        hasattr(response.candidates[0].grounding_metadata, 'search_entry_point')):
        print("\nSearch metadata:")
        print("-" * 50)
        print(response.candidates[0].grounding_metadata.search_entry_point.rendered_content)

except Exception as e:
    print(f"Error occurred: {e}")
    print("Make sure your API key is valid and you have the necessary permissions.")





