import { app, HttpRequest, HttpResponseInit } from '@azure/functions';
import { CosmosClient } from '@azure/cosmos';
import pino from 'pino';
import { z } from 'zod';

const logger = pino({ name: 'feedback-handler' });

const feedbackInputSchema = z
  .object({
    queryId: z.string().trim().min(1, 'queryId is required'),
    rating: z.number().int().min(1).max(5),
    comment: z.string().trim().min(1).max(2000),
    attendantEmail: z.string().email(),
  })
  .strict();

type FeedbackInput = z.infer<typeof feedbackInputSchema>;

type FeedbackDocument = FeedbackInput & {
  timestamp: string;
};

const cosmosConnectionString = process.env.COSMOS_CONNECTION_STRING;
const cosmosClient = cosmosConnectionString
  ? new CosmosClient(cosmosConnectionString)
  : null;

async function persistFeedback(document: FeedbackDocument): Promise<void> {
  if (!cosmosClient) {
    throw new Error('COSMOS_CONNECTION_STRING is not configured');
  }

  const database = cosmosClient.database('novatech');
  const container = database.container('feedbacks');

  await container.items.create(document);
}

function parseFeedbackPayload(payload: unknown): FeedbackInput {
  const parsed = feedbackInputSchema.safeParse(payload);

  if (!parsed.success) {
    logger.warn(
      {
        event: 'feedback_validation_failed',
        issues: parsed.error.issues,
      },
      'Invalid feedback payload'
    );
    throw new Error('Invalid feedback payload');
  }

  return parsed.data;
}

export async function feedbackHandler(
  request: HttpRequest
): Promise<HttpResponseInit> {
  try {
    const payload = await request.json();
    const feedback = parseFeedbackPayload(payload);

    const feedbackDocument: FeedbackDocument = {
      ...feedback,
      timestamp: new Date().toISOString(),
    };

    await persistFeedback(feedbackDocument);

    logger.info(
      {
        event: 'feedback_persisted',
        queryId: feedback.queryId,
        rating: feedback.rating,
      },
      'Feedback stored'
    );

    return {
      status: 200,
      jsonBody: { ok: true },
    };
  } catch (error) {
    logger.error(
      {
        event: 'feedback_handler_failed',
        error: error instanceof Error ? error.message : 'unknown_error',
      },
      'Failed to process feedback'
    );

    return {
      status: 400,
      jsonBody: {
        ok: false,
        message: 'Invalid request',
      },
    };
  }
}

app.http('feedback', {
  methods: ['POST'],
  authLevel: 'function',
  handler: feedbackHandler,
});
