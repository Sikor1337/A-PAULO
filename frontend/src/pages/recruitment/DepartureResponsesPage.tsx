import { SurveyResponses } from '@/features/surveys';
import { useDepartureInterviews } from '@/hooks/useDepartures';

const DepartureResponsesPage = () => {
  const interviews = useDepartureInterviews();
  const records = (interviews.data ?? []).map((interview) => ({
    id: interview.id,
    title: interview.volunteer.full_name,
    subtitle: `Odejście: ${interview.departure_date}`,
    summary: interview.departure_reason,
    answers: interview.answers,
    source: interview,
  }));

  return (
    <SurveyResponses
      title="Zapisane ankiety odejścia"
      description="Pełne odpowiedzi z ankiet odejścia wolontariuszy."
      records={records}
      isLoading={interviews.isLoading}
      emptyText="Brak zapisanych ankiet."
    />
  );
};

export default DepartureResponsesPage;
