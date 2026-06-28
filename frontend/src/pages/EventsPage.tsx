import PageShell from '@/components/layout/PageShell';

const CALENDAR_EMBED_URL =
  'https://calendar.google.com/calendar/embed?src=projektapaulo%40gmail.com&ctz=Europe%2FWarsaw';

const EventsPage = () => (
  <PageShell cardClassName="min-h-[calc(100dvh-88px)] rounded-xl bg-white p-4 shadow-lg sm:p-6 lg:min-h-[calc(100dvh-48px)]">
    <header className="mb-5">
      <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">Wydarzenia</h1>
      <p className="mt-1 text-sm text-gray-500">Kalendarz Google PaP</p>
    </header>

    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white">
      <iframe
        title="Kalendarz wydarzeń PaP"
        src={CALENDAR_EMBED_URL}
        className="h-[70dvh] min-h-[600px] w-full"
        style={{ border: 0 }}
        frameBorder="0"
        scrolling="no"
        loading="lazy"
      />
    </div>
  </PageShell>
);

export default EventsPage;
