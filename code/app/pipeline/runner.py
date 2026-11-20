"""
Step 4 (+5): run each attack and judge the reply.

Two modes:
- predicted: Claude predicts how a typical bot with this system prompt would
  reply. These replies are labelled "predicted" everywhere. They are NOT
  real results.
- live: the attack is sent to the user's real chatbot endpoint and the real
  reply is recorded.

Either way, a separate judge call then marks the reply Pass or Fail.
Attacks run a few at a time in parallel threads to save waiting time.
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from app import config, prompts
from app.live_client import LiveClientError, send_attack
from app.llm import LLMClient
from app.pipeline.judge import judge_reply
from app.schemas import Analysis, Attack, AttackResult, LiveConfig, Mode, PredictedReply, Reply


def get_reply(
    llm: LLMClient, mode: Mode, system_prompt: str, attack: Attack, live: Optional[LiveConfig]
) -> Reply:
    """Get the bot's reply to one attack, in the chosen mode."""
    if mode == "predicted":
        predicted = llm.structured(
            task="predict",
            system=prompts.PREDICT_SYSTEM,
            user=prompts.predict_user(system_prompt, attack),
            output_model=PredictedReply,
        )
        return Reply(attack_id=attack.id, mode="predicted", text=predicted.predicted_reply)

    # Live mode
    if live is None:
        raise ValueError("Live mode needs an endpoint configuration.")
    try:
        text = send_attack(live, attack.prompt, system_prompt)
        return Reply(attack_id=attack.id, mode="live", text=text)
    except LiveClientError as exc:
        return Reply(attack_id=attack.id, mode="live", text="", error=str(exc))


def run_one(
    llm: LLMClient, mode: Mode, system_prompt: str, analysis: Analysis,
    attack: Attack, live: Optional[LiveConfig],
) -> AttackResult:
    """Run one attack, then judge it (unless it could not be run)."""
    reply = get_reply(llm, mode, system_prompt, attack, live)
    if reply.error:
        return AttackResult(attack=attack, reply=reply)
    judgment, verified = judge_reply(llm, system_prompt, analysis, attack, reply.text)
    return AttackResult(attack=attack, reply=reply, judgment=judgment, evidence_verified=verified)


def run_attacks(
    llm: LLMClient, mode: Mode, system_prompt: str, analysis: Analysis,
    attacks: list[Attack], live: Optional[LiveConfig] = None,
) -> list[AttackResult]:
    """Run every attack and return results in the same order as the attacks."""
    with ThreadPoolExecutor(max_workers=config.MAX_PARALLEL_ATTACKS) as pool:
        futures = [pool.submit(run_one, llm, mode, system_prompt, analysis, a, live) for a in attacks]
        # .result() re-raises any error from the thread, e.g. an LLMError.
        return [f.result() for f in futures]
