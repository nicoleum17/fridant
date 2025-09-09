using UnityEngine;
using TMPro;
using UnityEditorInternal;

public class TextEditor : MonoBehaviour
{
    public TextMeshProUGUI lostVictims;
    public void Update()
    {
        if (GameManager.Instance != null && GameManager.Instance.CurrentState != null)
        {
            SimulationState state = GameManager.Instance.CurrentState;
            lostVictims.text = $"Victims Lost: {state.model_data.lost_victims}";
        }

    }

}
