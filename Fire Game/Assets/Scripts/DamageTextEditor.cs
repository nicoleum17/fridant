using UnityEngine;
using TMPro;
using UnityEditorInternal;

public class DamageTextEditor : MonoBehaviour
{
    public TextMeshProUGUI damage;
    public void Update()
    {
        if (GameManager.Instance != null && GameManager.Instance.CurrentState != null)
        {
            SimulationState state = GameManager.Instance.CurrentState;
            damage.text = $"Damage Counters: {state.model_data.damage}";
        }

    }

}
