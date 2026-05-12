package br.ufpb.dsc.cirurgias.repository;

import br.ufpb.dsc.cirurgias.domain.Hospital;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface HospitalRepository extends JpaRepository<Hospital, Long> {
}
