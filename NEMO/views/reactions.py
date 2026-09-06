from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from NEMO.models import (
    Comment,
    SafetyIssue,
    StaffKnowledgeBaseItem,
    Task,
    User,
    UserKnowledgeBaseItem,
    UserReaction,
    set_user_reaction,
)

# Models that support user reactions, and the permission check required for a user to react to an instance of them.
REACTABLE_MODELS = {
    "task": (Task, lambda user, obj: True),
    "safetyissue": (SafetyIssue, lambda user, obj: True),
    "comment": (Comment, lambda user, obj: True),
    "userknowledgebaseitem": (UserKnowledgeBaseItem, lambda user, obj: True),
    "staffknowledgebaseitem": (StaffKnowledgeBaseItem, lambda user, obj: user.is_any_part_of_staff),
}


@login_required
@require_POST
def toggle_reaction(request, model_name: str, object_id: int):
    model_name = model_name.lower()
    if model_name not in REACTABLE_MODELS:
        return HttpResponseBadRequest("Unsupported content type for reactions.")
    model_class, is_authorized = REACTABLE_MODELS[model_name]
    obj = get_object_or_404(model_class, id=object_id)
    user: User = request.user
    if not is_authorized(user, obj):
        return HttpResponseBadRequest("You are not authorized to react to this item.")
    try:
        reaction = int(request.POST.get("reaction", UserReaction.Reaction.HELPFUL))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Invalid reaction value.")
    if reaction not in dict(UserReaction.Reaction.Choices):
        return HttpResponseBadRequest("Invalid reaction value.")
    current_reaction, counts = set_user_reaction(obj, user, reaction)
    return JsonResponse({"reaction": current_reaction, **counts})
