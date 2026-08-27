#!/usr/bin/env bash

API_URL="http://rag.akimovp.ru/api/v1/query"

HAS_JQ=$(command -v jq >/dev/null 2>&1 && echo "yes" || echo "no")

echo "=================================================="
echo " Starting RAG Service Benchmark (Qwen2.5-1.5B)"
echo " API Endpoint: $API_URL"
echo "=================================================="
echo ""

questions=(
    "Who proposed an amendment to the Missouri bill that required the territory to gradually outlaw slavery?"
    "How did Henry Brown manage to escape to the north?"
    "How many extra members of Congress did the Three-fifths Compromise give to the South by 1819?"
    "Which state was allowed to enter the Union as a free state to break the deadlock over Missouri in 1820?"
    "Who was the most famous conductor of the Underground Railroad?"
    "What table rule involving a dish of salt was used to show social rank in colonial America?"
    "How did the legal rights of married women in New Netherland differ from those in English colonies?"
    "Between 1492 and 1820, how did the number of enslaved Africans arriving in the Americas compare to European immigrants?"
    "Why did the Dutch force the surrendering Swedes to march with musket balls in their mouths?"
    "Prior to 1715, were more Indian slaves exported from America or African slaves imported, and what town was the center of this trade?"
    "What was the title of the pamphlet written by Thomas Paine?"
    "Who warned the countryside that British troops were coming to Concord?"
    "What goods did the colonists throw into the harbor during the Boston Tea Party?"
    "What law forbade colonists from settling west of the Appalachian Mountains?"
    "What were British soldiers called by angry local colonists because of their red coats?"
    "Did Thomas Jefferson list natural rights in the first draft of the Declaration of Independence exactly as John Locke had formulated them?"
    "Which hill overlooking Boston did the colonial militias actually fortify prior to the redcoats retaking it the next day?"
    "Why did General Washington cross the ice-filled Delaware River back on Christmas Eve in 1776?"
    "What major military event directly convinced France to join the United States as an official ally in the war?"
    "Did Thomas Jefferson free his own slaves after establishing the principle of equality in the Declaration of Independence?"
    "Why did the British forces refrain from fully utilizing enslaved African Americans to fight against their masters in the South?"
)

expected_answers=(
    "James Tallmadge"
    "He had himself sealed in a wooden crate and shipped north"
    "Seventeen (17)"
    "Maine"
    "Harriet Tubman"
    "People of higher rank sat above the salt, while others sat below it."
    "In New Netherland, women kept their maiden names and could sign business contracts, whereas in English colonies husbands held legal rights over property and contracts."
    "Five times as many enslaved Africans came to the Americas as all European immigrants combined."
    "To remind the Swedes that the Dutch had the power to shoot them all if they pleased."
    "More Indian slaves were shipped out (30,000 to 50,000) than African slaves brought in; Charles Town was the center."
    "Common Sense"
    "Paul Revere (along with several other men)"
    "Tea"
    "The Proclamation of 1763"
    "Lobsterbacks"
    "No, Jefferson omitted 'health' and replaced 'possessions' with 'the pursuit of Happiness'."
    "Breed's Hill (even though they originally planned to take Bunker Hill)."
    "To carry out a surprise attack on the Hessian garrison at Trenton, New Jersey."
    "The disastrous defeat and surrender of General Burgoyne's entire army at Saratoga."
    "No, although he was uneasy about slavery throughout his life, he never actually freed his slaves."
    "Most British officers and white Loyalists were uncomfortable with the idea of using slaves to fight against white masters."
)

total_start_ms=$(date +%s%3N)

for i in "${!questions[@]}"; do
    num=$((i + 1))
    q="${questions[$i]}"
    exp="${expected_answers[$i]}"

    echo "--------------------------------------------------"
    echo "Test #$num"
    echo "Question: $q"
    echo "Expected: $exp"
    echo "--------------------------------------------------"

    payload=$(cat <<EOF
{
  "question": "$q",
  "k": 3
}
EOF
    )

    start_ms=$(date +%s%3N)

    if [ "$HAS_JQ" = "yes" ]; then
        curl -s -X POST "$API_URL" \
             -H "Content-Type: application/json" \
             -d "$payload" | jq '.'
    else
        curl -s -X POST "$API_URL" \
             -H "Content-Type: application/json" \
             -d "$payload"
        echo ""
    fi

    end_ms=$(date +%s%3N)

    elapsed_ms=$((end_ms - start_ms))
    elapsed_sec=$(awk -v ms="$elapsed_ms" 'BEGIN {printf "%.3f", ms/1000}')

    echo "Time spent: ${elapsed_sec}s (${elapsed_ms} ms)"
    echo ""
done

total_end_ms=$(date +%s%3N)
total_elapsed_ms=$((total_end_ms - total_start_ms))
total_elapsed_sec=$(awk -v ms="$total_elapsed_ms" 'BEGIN {printf "%.3f", ms/1000}')

echo "=================================================="
echo " Benchmark completed!"
echo " Total infer time for all tests: ${total_elapsed_sec}s (${total_elapsed_ms} ms)"
echo "=================================================="