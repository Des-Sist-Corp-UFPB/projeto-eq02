package br.ufpb.dsc.cirurgias.repository;

import br.ufpb.dsc.cirurgias.domain.Paciente;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface PacienteRepository extends JpaRepository<Paciente, Long> {
}
