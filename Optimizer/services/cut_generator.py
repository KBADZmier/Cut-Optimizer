from typing import List

from models.order import FrameOrder
from models.cutting import Cut
from tests.test_frame import orders

def generate_cuts(
    orders: List[FrameOrder],
) -> List[Cut]:

    cuts: List[Cut] = []

    cut_id = 1

    for order in orders:

        length = (
            order.length_mm
            - order.reduction_mm
        )

        height = (
            order.height_mm
            - order.reduction_mm
        )

        if order.has_drip_cap:
            height -= order.drip_cap_reduction_mm

        if length <= 0:
            raise ValueError(
                f"{order.name}: "
                f"długość po pomniejszeniu "
                f"musi być większa od 0."
            )

        if height <= 0:
            raise ValueError(
                f"{order.name}: "
                f"wysokość po pomniejszeniu "
                f"musi być większa od 0."
            )

        for _ in range(order.quantity):

            # Dwa elementy poziome
            for _ in range(2):

                cuts.append(
                    Cut(
                        id=cut_id,
                        frame_name=order.name,
                        side="długość",
                        length_mm=round(length, 1),
                        color=order.color,
                    )
                )

                cut_id += 1

            for _ in range(2):

                cuts.append(
                    Cut(
                        id=cut_id,
                        frame_name=order.name,
                        side="wysokość",
                        length_mm=round(height, 1),
                        color=order.color,
                    )
                )

                cut_id += 1

    return cuts