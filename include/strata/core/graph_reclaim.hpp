#pragma once
#include <functional>
#include <string>
#include <utility>

namespace strata::core {
using GraphReclaim = std::function<bool(bool&, std::string&)>;
struct GraphReclaimSlot {
    void* owner = nullptr;
    GraphReclaim reclaim;
    GraphReclaimSlot* previous = nullptr;
};
inline thread_local GraphReclaimSlot* graph_reclaim_slot = nullptr;

// Only a serial serve loop enables this scope. Other threads/backends retain their allocation policy.
class GraphReclaimScope {
    GraphReclaimSlot slot_;
public:
    explicit GraphReclaimScope(bool enabled) {
        slot_.previous = graph_reclaim_slot;
        graph_reclaim_slot = enabled ? &slot_ : nullptr;
    }
    ~GraphReclaimScope() { graph_reclaim_slot = slot_.previous; }
    GraphReclaimScope(const GraphReclaimScope&) = delete;
    GraphReclaimScope& operator=(const GraphReclaimScope&) = delete;
};
inline void register_graph_reclaim(void* owner, GraphReclaim reclaim) {
    if (graph_reclaim_slot && graph_reclaim_slot->owner != owner) {
        graph_reclaim_slot->owner = owner;
        graph_reclaim_slot->reclaim = std::move(reclaim);
    }
}
inline void clear_graph_reclaim(void* owner) {
    for (auto* slot = graph_reclaim_slot; slot; slot = slot->previous) {
        if (slot->owner == owner) { slot->owner = nullptr; slot->reclaim = {}; }
    }
}
inline bool reclaim_graph_memory(bool& freed, std::string& err) {
    freed = false;
    return !graph_reclaim_slot || !graph_reclaim_slot->reclaim || graph_reclaim_slot->reclaim(freed, err);
}
}  // namespace strata::core
